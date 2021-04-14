import sys
import logging
import concurrent.futures
import os

import numpy as np
import itertools as it

from typing import Iterator, Any, Literal
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

SimConf = dict[Literal["general", "space", "environment"], dict[str, Any]]
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
            request_generator=[RequestGeneratorCls],
            rate=[10],
            max_pickup_delay=[3],
            max_pickup_delivery_delay_rel=[1.9],
            seed=[42],
        ),
        environment=dict(
            TransportationRequestCls=[TransportationRequestCls],
            VehicleStateCls=[VehicleStateCls],
            FleetStateCls=[FleetStateCls],
        ),
    )


def perform_single_simulation(params):
    space = params["general"]["space"]

    rg = RandomRequestGenerator(
        rate=params["request_generator"]["rate"],
        max_pickup_delay=params["request_generator"]["max_pickup_delay"],
        max_delivery_delay_rel=params["request_generator"]["max_pickup_delay"],
        seed=params["request_generator"]["seed"],
        space=space,
        request_class=params["environment"]["TransportationRequestCls"],
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
    print(f"Simulating run on process {os.getpid()} @ \n{params!r}\n")

    simulation = fs.simulate(it.islice(rg, params["general"]["n_reqs"]))

    sim_id = get_uuid()
    data_dir = params["environment"].get("data_dir", Path())
    jsonl_path = data_dir / f"{sim_id}.jsonl"
    param_path = data_dir / f"{sim_id}_params.json"

    assert not jsonl_path.exists()
    assert not param_path.exists()

    save_params_json(param_path=param_path, params=params)

    while chunk := list(
        it.islice(simulation, params["environment"].get("chunksize", 1000))
    ):
        save_events_json(jsonl_path=jsonl_path, events=chunk)

    return sim_id


def simulate_parameter_space(
    *,
    data_dir: Path,
    conf: ParamScanConf,
    chunksize: int = 1000,
    process_chunksize: int = 1,
    max_workers=None,
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
    chunksize
        Maximum number of events to keep in memory before saving to disk
    process_chunksize
        Number of simulations to submit to a process in the process pool at a time
    max_workers
        Defaults to number of processors on the machine if `None` or not given.

    Returns
    -------
    List of simulation UUIDs.
    Results can be accessed by reading `data_dir / f"{sim_uuid}.jsonl"`,
    parameters at `data_dir / f"{sim_uuid}_params.json"`
    """

    conf["environment"]["data_dir"] = [data_dir]
    conf["environment"]["chunksize"] = [chunksize]

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        sim_ids = list(
            executor.map(
                perform_single_simulation,
                param_scan(conf),
                chunksize=process_chunksize,
            )
        )

    return sim_ids
