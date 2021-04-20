from collections import defaultdict
from copy import deepcopy

import abc
import operator as op

import sys
import logging
import concurrent.futures
import os
import hashlib

import functools as ft
import itertools as it

from typing import Iterator, Any, Optional, Literal, Dict, Iterable
from pathlib import Path

from thesimulator.util.dispatchers import (
    brute_force_total_traveltime_minimizing_dispatcher as brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.dispatchers_cython import (
    brute_force_total_traveltime_minimizing_dispatcher as cy_brute_force_total_traveltime_minimizing_dispatcher,
)
from thesimulator.util.spaces import Euclidean2D
from thesimulator.util.spaces_cython import Euclidean2D as CyEuclidean2D
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.data_structures import (
    TransportationRequest,
)
from thesimulator.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
)
from thesimulator.vehicle_state import VehicleState
from thesimulator.vehicle_state_cython import VehicleState as CyVehicleState
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.extras.io import (
    create_params_json,
    save_events_json,
)

logger = logging.getLogger(__name__)


def iterate_zip_product(
    *, params_to_product: Optional[dict] = None, params_to_zip: Optional[dict] = None
):
    """
    Returns an iterator of parameter combinations, just like `.param_scan_cartesian_product`. However, allows the user
    to specify an arbitrary combination of parameters that should not be part of the cartesian product, but rather
    always appear as a fixed combination.

    Examples
    --------

    .. code-block:: python

        >>> params_to_zip = {1: {"a": [8,9], "b": [88, 99]}}
        >>> params = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
        >>> tuple(iterate_zip_product(params_to_zip=params_to_zip, params=params))
        (
           {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 1000}},
           {1: {"a": 8, "b": 88, "c": 100}, 2: {"z": 2000}},
           {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 1000}},
           {1: {"a": 8, "b": 88, "c": 200}, 2: {"z": 2000}},
           {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 1000}},
           {1: {"a": 9, "b": 99, "c": 100}, 2: {"z": 2000}},
           {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 1000}},
           {1: {"a": 9, "b": 99, "c": 200}, 2: {"z": 2000}},
        ),


    Parameters
    ----------
    params_to_zip
        A dict of dict like the argument of `.param_scan_cartesian_product`. However, a subset of the keys can be
        supplied. The values for each inner dict should be lists that all match in lengths. In the returned iterator,
        these parameters will be :func:`zipped <python:zip>` together, i.e. they will vary together.
    params_to_product
        A dict of dict like the argument of `.param_scan_cartesian_product`. However, a subset of the keys can be
        supplied. All possible combinations of these parameters will be generated.
    Returns
    -------
        An Iterator of parameter combinations that can be passed to `simulate_parameter_combinations`.

    """
    outer_keys = set(params_to_zip) | set(params_to_product)
    if params_to_zip:
        zipped_params_iter = zip(
            *(
                params_to_zip[outer_key][inner_key]
                for outer_key in params_to_zip.keys()
                for inner_key in params_to_zip[outer_key].keys()
            )
        )

        zipped_keypairs = [
            (outer_key, inner_key)
            for outer_key in params_to_zip.keys()
            for inner_key in params_to_zip[outer_key].keys()
        ]
    else:
        zipped_params_iter = zipped_keypairs = [tuple()]

    if params_to_product:
        producted_params_iter = it.product(
            *(
                params_to_product[outer_key][inner_key]
                for outer_key in params_to_product.keys()
                for inner_key in params_to_product[outer_key].keys()
            )
        )
        producted_keypairs = [
            (outer_key, inner_key)
            for outer_key in params_to_product.keys()
            for inner_key in params_to_product[outer_key].keys()
        ]
    else:
        producted_params_iter = producted_keypairs = [tuple()]

    for zipped_params, producted_params in it.product(
        zipped_params_iter, producted_params_iter
    ):
        d = {outer_key: dict() for outer_key in outer_keys}

        for (u, v), p in zip(zipped_keypairs, zipped_params):
            d[u][v] = p

        for (u, v), p in zip(producted_keypairs, producted_params):
            d[u][v] = p

        yield d


def perform_single_simulation(params, *, data_dir, chunksize=1000, debug=False):
    # we need a pseudorandom id that does not change if this function is called with the same params
    # the following does not guarantee a lack of collisions, and will fail if non-ascii characters are involved.

    params_json = create_params_json(params=params)
    sim_id = hashlib.sha224(params_json.encode("ascii", errors="strict")).hexdigest()
    jsonl_path = data_dir / f"{sim_id}.jsonl"
    param_path = data_dir / f"{sim_id}_params.json"

    if param_path.exists():
        # assume that a previous simulation run already exists. this works because we write
        # to param_path *after* a successful simulation run.
        logger.info(
            f"Pre-existing param json exists for {params=}, skipping simulation"
        )
        return sim_id
    else:
        logger.info(
            f"No pre-existing param json exists for {params=}, running simulation"
        )
        if jsonl_path.exists():
            logger.info(
                "Potentially incomplete simulation data exists, this will be overwritten"
            )

    space = params["general"]["space"]
    RequestGeneratorCls = params["request_generator"].pop("RequestGeneratorCls")
    rg = RequestGeneratorCls(
        space=space,
        request_class=params["environment"]["TransportationRequestCls"],
        **params["request_generator"],
    )

    fs = params["environment"]["FleetStateCls"](
        initial_locations={
            vehicle_id: params["general"]["initial_location"]
            for vehicle_id in range(params["general"]["n_vehicles"])
        },
        space=space,
        dispatcher=params["general"]["dispatcher"],
        seat_capacities=params["general"]["seat_capacity"],
        vehicle_state_class=params["environment"]["VehicleStateCls"],
    )

    # NOTE: this string is matched for testing
    if debug:
        print(f"Simulating run on process {os.getpid()} @ \n{params!r}\n")

    simulation = fs.simulate(it.islice(rg, params["general"]["n_reqs"]))

    while chunk := list(it.islice(simulation, chunksize)):
        save_events_json(jsonl_path=jsonl_path, events=chunk)

    with open(str(param_path), "w") as f:
        f.write(params_json)
    return sim_id


class SimulationSet:
    """
    Specifies a parameter space that should be scanned to generate an iterable of `SimConf` objects.
    """

    @staticmethod
    def _two_level_dict_update(base_dict: dict, update_dict: dict) -> dict:
        d = deepcopy(base_dict)
        for outer_key in set(base_dict) | set(update_dict):
            d[outer_key] = base_dict.get(outer_key, {}) | update_dict.get(outer_key, {})
        return d

    @staticmethod
    def _zip_params_equal_length(zip_params):
        return ft.reduce(
            op.__eq__,
            (
                len(inner_value)
                for inner_dict in zip_params.values()
                for inner_value in inner_dict
            ),
        )

    def __init__(
        self,
        *,
        base_params: Optional[dict] = None,
        zip_params: Optional[dict] = None,
        product_params: Optional[dict] = None,
        cython: bool = True,
        mpi: bool = False,
        debug: bool = False,
        max_workers: Optional[int] = None,
        process_chunksize: int = 1,
    ):
        """
        For more detail see :ref:`Parameter Scan Configuration`.

        Parameters
        ----------
        cython
            If True, use cython types.
        mpi
            If True use MPIFuturesFleetState for parallelization.

        Returns
        -------

        """

        self.debug = debug
        self.max_workers = max_workers
        self.process_chunksize = process_chunksize

        if cython:
            SpaceObj = CyEuclidean2D()
            dispatcher = cy_brute_force_total_traveltime_minimizing_dispatcher
            TransportationRequestCls = CyTransportationRequest
            VehicleStateCls = CyVehicleState
        else:
            SpaceObj = Euclidean2D()
            dispatcher = brute_force_total_traveltime_minimizing_dispatcher
            TransportationRequestCls = TransportationRequest
            VehicleStateCls = VehicleState

        if mpi:
            FleetStateCls = MPIFuturesFleetState
        else:
            FleetStateCls = SlowSimpleFleetState

        RequestGeneratorCls = RandomRequestGenerator

        self._base_params = dict(
            general=dict(
                n_reqs=100,
                space=SpaceObj,
                n_vehicles=10,
                initial_location=(0, 0),
                seat_capacity=8,
                dispatcher=dispatcher,
                TransportationRequestCls=TransportationRequestCls,
                VehicleStateCls=VehicleStateCls,
                FleetStateCls=FleetStateCls,
            ),
            request_generator=dict(
                RequestGeneratorCls=RequestGeneratorCls,
                rate=10,
                max_pickup_delay=3,
                max_delivery_delay_rel=1.9,
                seed=42,
            ),
        )

        # assert no unknown outer keys
        assert not (set(base_params) | set(zip_params) | set(product_params)) - set(
            self._base_params
        ), "invalid outer key"

        # assert no unknown inner keys
        for outer_key in self._base_params:
            assert not (
                set(base_params.get(outer_key, {}))
                | set(zip_params.get(outer_key, {}))
                | set(product_params.get(outer_key, {}))
            ) - set(self._base_params[outer_key]), f"invalid inner key for {outer_key=}"

        # assert equal length of zipped parameters
        assert self._zip_params_equal_length(
            zip_params
        ), "zipped parameters must be of equal length"

        self._base_params = self._two_level_dict_update(self._base_params, base_params)
        self._zip_params = zip_params if zip_params is not None else {}
        self._product_params = product_params if product_params is not None else {}

        self._result_ids = None

    @property
    def result_ids(self):
        return self._result_ids if self._result_ids is not None else []

    @staticmethod
    def _make_joined_key_pairs_values(*, params, join_fn):
        """

        Parameters
        ----------
        params
        join_fn

        Returns
        -------
        joined_key_pairs, joined_values_iter
        """
        if params:
            joined_values_iter = join_fn(
                *(
                    params[outer_key][inner_key]
                    for outer_key in params.keys()
                    for inner_key in params[outer_key].keys()
                )
            )
            joined_key_pairs = [
                (outer_key, inner_key)
                for outer_key in params.keys()
                for inner_key in params[outer_key].keys()
            ]
        else:
            joined_values_iter = joined_key_pairs = [tuple()]

        return joined_key_pairs, joined_values_iter

    def run(self):
        zipped_key_pairs, zipped_values_iter = self._make_joined_key_pairs_values(
            params=self._zip_params, join_fn=zip
        )
        (
            multiplied_key_pairs,
            multiplied_values_iter,
        ) = self._make_joined_key_pairs_values(
            params=self._product_params, join_fn=it.product
        )

        def param_combinations():
            for zipped_params, multiplied_params in it.product(
                zipped_values_iter, multiplied_values_iter
            ):
                d = defaultdict(dict)

                for (outer_key, inner_key), value in zip(
                    zipped_key_pairs, zipped_params
                ):
                    d[outer_key][inner_key] = value

                for (outer_key, inner_key), value in zip(
                    multiplied_key_pairs, multiplied_params
                ):
                    d[outer_key][inner_key] = value

                yield self._two_level_dict_update(self._base_params, d)

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            self._result_ids = list(
                executor.map(
                    ft.partial(perform_single_simulation, debug=self.debug),
                    param_combinations,
                    chunksize=self.process_chunksize,
                )
            )

    def __len__(self):
        zip_part = len(next(iter(next(iter(self._zip_params.values())).values())))
        product_part = ft.reduce(
            op.mul,
            (
                len(inner_value)
                for inner_dict in self._product_params.values()
                for inner_value in inner_dict
            ),
        )
        return zip_part * product_part


# def simulate_parameter_combinations(
#     *,
#     param_combinations: Iterator[SimConf],
#     process_chunksize: int = 1,
#     max_workers=None,
#     debug=False,
# ):
#     """
#     Run simulations for different parameter combinations. See the docstring of `.simulate_parameter_space` for more details.
#
#     Parameters
#     ----------
#     param_combinations
#         An iterable of parameter configurations. For more detail see :ref:`Executing Simulations`
#     process_chunksize
#     max_workers
#     debug
#         See the  docstring of `.simulate_parameter_space`
#
#     Returns
#     -------
#         See the  docstring of `.simulate_parameter_space`
#     """
#     with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
#         sim_ids = list(
#             executor.map(
#                 ft.partial(perform_single_simulation, debug=debug),
#                 param_combinations,
#                 chunksize=process_chunksize,
#             )
#         )
#     return sim_ids


# def simulate_parameter_space(
#     *,
#     data_dir: Path,
#     param_space_to_product: ParamScanConf,
#     param_space_to_zip: Optional[ParamScanConf] = None,
#     chunksize: int = 1000,
#     process_chunksize: int = 1,
#     max_workers=None,
#     debug=False,
# ):
#     """
#     Run a parameter scan of simulations and save emitted events to disk in JSON Lines format
#     and additional JSON file containing the simulation parameters. Parallelization is accomplished
#     by multiprocessing. For more detail see :ref:`Executing Simulations`.
#
#     Parameters
#     ----------
#     data_dir
#         path to the desired output directory
#     param_combinations
#         iterator of single simulation configurations. see :ref:`Parameter Scan Configuration` for details.
#     chunksize
#         Maximum number of events to keep in memory before saving to disk
#     process_chunksize
#         Number of simulations to submit to a process in the process pool at a time
#     max_workers
#         Defaults to number of processors on the machine if `None` or not given.
#     debug
#         Print multiprocessing debug info.
#
#     Returns
#     -------
#     List of simulation UUIDs.
#     Results can be accessed by reading `data_dir / f"{sim_uuid}.jsonl"`,
#     parameters at `data_dir / f"{sim_uuid}_params.json"`
#     """
#     param_space_to_product["environment"]["data_dir"] = [data_dir]
#     param_space_to_product["environment"]["chunksize"] = [chunksize]
#
#     if param_space_to_zip is None:
#         param_space_to_zip = dict()
#
#     return simulate_parameter_combinations(
#         param_combinations=iterate_zip_product(
#             params=param_space_to_product, params_to_zip=param_space_to_zip
#         ),
#         process_chunksize=process_chunksize,
#         max_workers=max_workers,
#         debug=debug,
#     )
