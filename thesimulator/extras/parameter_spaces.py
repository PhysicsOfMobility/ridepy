import sys
import logging
import concurrent.futures
import os
import hashlib

import functools as ft
import itertools as it

from typing import Iterator, Any, Optional, Literal, Dict
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
from thesimulator.util import get_uuid
from thesimulator.extras.io import (
    create_params_json,
    save_params_json,
    save_events_json,
)

logger = logging.getLogger(__name__)

SimConf = Dict[Literal["general", "space", "environment"], Dict[str, Any]]
"""Specifies the parameter combinations for a single simulation run."""

ParamScanConf = Dict[Literal["general", "space", "environment"], Dict[str, list[Any]]]
"""Specifies a parameter space that should be scanned to generate an iterable of `SimConf` objects."""


def param_scan(
    params_to_product: ParamScanConf, params_to_zip: ParamScanConf
) -> Iterator[SimConf]:
    """
    Returns an iterator of parameter combinations, just like `.param_scan_cartesian_product`. However, allows the user
    to specify an arbitrary combination of parameters that should not be part of the cartesian product, but rather
    always appear as a fixed combination.

    Examples
    --------

    .. code-block:: python

        >>> params_to_zip = {1: {"a": [8,9], "b": [88, 99]}}
        >>> params_to_product = {1: {"c": [100, 200]}, 2: {"z": [1000, 2000]}}
        >>> tuple(param_scan(params_to_zip=params_to_zip, params_to_product=params_to_product))
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
    outer_keys = set(params_to_zip.keys()) | set(params_to_product.keys())
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


def get_default_conf(cython: bool = True, mpi: bool = False) -> ParamScanConf:
    """
    Return default parameter scan configuration as dict.
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

    return dict(
        general=dict(
            n_reqs=[100],
            space=[SpaceObj],
            n_vehicles=[10],
            initial_location=[(0, 0)],
            seat_capacity=[8],
            dispatcher=[dispatcher],
        ),
        request_generator=dict(
            RequestGeneratorCls=[RequestGeneratorCls],
            rate=[10],
            max_pickup_delay=[3],
            max_delivery_delay_rel=[1.9],
            seed=[42],
        ),
        environment=dict(
            TransportationRequestCls=[TransportationRequestCls],
            VehicleStateCls=[VehicleStateCls],
            FleetStateCls=[FleetStateCls],
        ),
    )


def perform_single_simulation(params, debug):
    # we need a pseudorandom id that does not change if this function is called with the same params
    # the following does not guarantee a lack of collisions, and will fail if non-ascii characters are involved.

    params_json = create_params_json(params=params)
    sim_id = hashlib.sha224(params_json.encode("ascii", errors="strict")).hexdigest()
    data_dir = params["environment"].get("data_dir", Path())
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

    while chunk := list(
        it.islice(simulation, params["environment"].get("chunksize", 1000))
    ):
        save_events_json(jsonl_path=jsonl_path, events=chunk)

    with open(str(param_path), "w") as f:
        f.write(params_json)
    return sim_id


def simulate_parameter_combinations(
    *,
    param_combinations: Iterator[SimConf],
    process_chunksize: int = 1,
    max_workers=None,
    debug=False,
):
    """
    Run simulations for different parameter combinations. See the docstring of `.simulate_parameter_space` for more details.

    Parameters
    ----------
    param_combinations
        An iterable of parameter configurations. For more detail see :ref:`Executing Simulations`
    process_chunksize
    max_workers
    debug
        See the  docstring of `.simulate_parameter_space`

    Returns
    -------
        See the  docstring of `.simulate_parameter_space`
    """
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        sim_ids = list(
            executor.map(
                ft.partial(perform_single_simulation, debug=debug),
                param_combinations,
                chunksize=process_chunksize,
            )
        )
    return sim_ids


def simulate_parameter_space(
    *,
    data_dir: Path,
    param_space_to_product: ParamScanConf,
    param_space_to_zip: Optional[ParamScanConf] = None,
    chunksize: int = 1000,
    process_chunksize: int = 1,
    max_workers=None,
    debug=False,
):
    """
    Run a parameter scan of simulations and save emitted events to disk in JSON Lines format
    and additional JSON file containing the simulation parameters. Parallelization is accomplished
    by multiprocessing. For more detail see :ref:`Executing Simulations`.

    Parameters
    ----------
    data_dir
        path to the desired output directory
    param_combinations
        iterator of single simulation configurations. see :ref:`Parameter Scan Configuration` for details.
    chunksize
        Maximum number of events to keep in memory before saving to disk
    process_chunksize
        Number of simulations to submit to a process in the process pool at a time
    max_workers
        Defaults to number of processors on the machine if `None` or not given.
    debug
        Print multiprocessing debug info.

    Returns
    -------
    List of simulation UUIDs.
    Results can be accessed by reading `data_dir / f"{sim_uuid}.jsonl"`,
    parameters at `data_dir / f"{sim_uuid}_params.json"`
    """
    param_space_to_product["environment"]["data_dir"] = [data_dir]
    param_space_to_product["environment"]["chunksize"] = [chunksize]

    if param_space_to_zip is None:
        param_space_to_zip = dict()

    return simulate_parameter_combinations(
        param_combinations=param_scan(
            params_to_product=param_space_to_product, params_to_zip=param_space_to_zip
        ),
        process_chunksize=process_chunksize,
        max_workers=max_workers,
        debug=debug,
    )
