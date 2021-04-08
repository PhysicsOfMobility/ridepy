from typing import Iterator, Any, Literal

import logging

import numpy as np
import itertools as it

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
    InternalRequest,
    StopAction,
    Stop,
)
from thesimulator.data_structures_cython import (
    TransportationRequest as CyTransportationRequest,
    InternalRequest as CyInternalRequest,
    StopAction as CyStopAction,
    Stop as CyStop,
)
from thesimulator.vehicle_state import VehicleState
from thesimulator.vehicle_state_cython import VehicleState as CyVehicleState
from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.util import get_uuid
from thesimulator.extras.io import save_params_json, save_events_json


logger = logging.getLogger(__name__)

SimConf = dict[Literal["general", "space"], dict[str, Any]]
ParamScanConf = dict[Literal["general", "space"], dict[str, list[Any]]]


def param_scan(outer_dict: ParamScanConf) -> Iterator:
    """
    Return an iterator over all parameter combinations of a configuration parameter dictionary
    which consists of an outer dictionary indexed by strings and containing inner dictionaries
    as values which are indexed by strings and contain lists of possible values for each parameter.

    For additional detail see :ref:`Parameter Scan Configuration`.

    Examples
    --------

    .. code-block:: python

        >>> conf = {
        >>>     "general": {"parameter_1": [1, 2], "parameter_2": ["a"]},
        >>>     "request_generator": {"parameter_1": [0, 5]},
        >>> tuple(param_scan(conf))
        (
           {
               "general": {"parameter_1": 1, "parameter_2": "a"},
               "request_generator": {"parameter_1": 0},
           },
           {
               "general": {"parameter_1": 2, "parameter_2": "a"},
               "request_generator": {"parameter_1": 0},
           },
           {
               "general": {"parameter_1": 1, "parameter_2": "a"},
               "request_generator": {"parameter_1": 5},
           },
           {
               "general": {"parameter_1": 2, "parameter_2": "a"},
               "request_generator": {"parameter_1": 0},
           },
        )

    Parameters
    ----------
    outer_dict

    Returns
    -------

    """
    # outer_dict = {outer_key1: inner_dict1, outer_key_2: inner_dict2, ...}
    # inner_dict1 = {inner_key1: inner_dict_values[1], inner_key2: inner_dict_values[2], ...}
    return (
        {
            outer_key: inner_dict
            for outer_key, inner_dict in zip(outer_dict, inner_dicts)
        }
        for inner_dicts in it.product(
            *map(
                lambda inner_dict: map(
                    lambda inner_dict_values: dict(zip(inner_dict, inner_dict_values)),
                    it.product(*inner_dict.values()),
                ),
                outer_dict.values(),
            )
        )
    )


def get_default_conf(cython: bool = True) -> ParamScanConf:
    """
    Return default parameter scan configuration as dict.
    For more detail see :ref:`Parameter Scan Configuration`.

    Parameters
    ----------
    cython
        If True, use cython

    Returns
    -------

    """
    if cython:
        SpaceObj = CyEuclidean2D()
        dispatcher = cy_brute_force_total_traveltime_minimizing_dispatcher
    else:
        SpaceObj = Euclidean2D()
        dispatcher = brute_force_total_traveltime_minimizing_dispatcher

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
            request_generator=[RequestGeneratorCls],
            rate=[10],
            max_pickup_delay=[3],
            max_pickup_delivery_delay_rel=[1.9],
        ),
    )


def simulate(
    *,
    data_dir: Path,
    conf: ParamScanConf,
    cython: bool = True,
    mpi: bool = False,
    chunksize: int = 1000,
):
    """
    Run a parameter scan of simulations and save emitted events to disk in JSON Lines format
    and additional JSON file containing the simulation parameters.
    For more detail see :ref:`Executing Simulations`.

    Parameters
    ----------
    data_dir
        path to the desired output directory
    conf
        configuration dict for the parameter scan.
    cython
        If True, use cython.
    mpi
        If True, use MPI for parallelization
    chunksize
        Maximum number of events to keep in memory before saving to disk

    Returns
    -------
    List of simulation UUIDs.
    Results can be accessed by reading `data_dir / f"{sim_uuid}.jsonl"`,
    parameters at `data_dir / f"{sim_uuid}_params.json"`
    """
    if cython:
        TransportationRequestCls = CyTransportationRequest
        VehicleStateCls = CyVehicleState
    else:
        TransportationRequestCls = TransportationRequest
        VehicleStateCls = VehicleState

    if mpi:
        FleetStateCls = MPIFuturesFleetState
    else:
        FleetStateCls = SlowSimpleFleetState

    sim_ids = []
    for i, params in enumerate(param_scan(conf)):
        space = params.get("general").get("space")

        rg = RandomRequestGenerator(
            rate=params["request_generator"]["rate"],
            max_pickup_delay=params["request_generator"]["max_pickup_delay"],
            max_delivery_delay_rel=params["request_generator"]["max_pickup_delay"],
            space=space,
            request_class=TransportationRequestCls,
        )

        fs = FleetStateCls(
            initial_locations={
                vehicle_id: params["general"]["initial_location"]
                for vehicle_id in range(params["general"]["n_vehicles"])
            },
            space=space,
            dispatcher=params["general"]["dispatcher"],
            seat_capacities=params["general"]["seat_capacity"],
            vehicle_state_class=VehicleStateCls,
        )

        logger.info(f"Simulating run {i} @ {params!r}\n")

        simulation = fs.simulate(it.islice(rg, params["general"]["n_reqs"]))

        sim_id = get_uuid()
        jsonl_path = data_dir / f"{sim_id}.jsonl"
        param_path = data_dir / f"{sim_id}_params.json"

        assert not jsonl_path.exists()
        assert not param_path.exists()

        save_params_json(param_path=param_path, params=params)
        sim_ids.append(sim_id)

        while chunk := list(it.islice(simulation, chunksize)):
            save_events_json(jsonl_path=jsonl_path, events=chunk)

    return sim_ids
