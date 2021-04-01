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

get_pscan = lambda conf: map(
    lambda x: dict(zip(conf[1], x)), it.product(*conf[1].values())
)


def get_default_conf(cython=True):
    """
    Return default parameter scan configuration as dict.
    Schema:
    `{'general': {param1: [value1, value2]}, 'request_generator':{param42: [value2]}}`

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
    conf: dict[dict],
    cython: bool = True,
    mpi: bool = False,
    chunksize: int = 1000,
):
    """
    Run a parameter scan of simulations and save emitted events to disk in JSON Lines format
    and additional JSON file containing the simulation parameters.

    Parameters
    ----------
    data_dir
        path to the desired output directory
    conf
        configuration dict for the parameter scan.
        Schema:
        `{'general': {param1: [value1, value2]}, 'request_generator':{param42: [value2]}}`
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

    param_scan = (
        {k: v for k, v in zip(conf.keys(), x)}
        for x in it.product(*map(get_pscan, conf.items()))
    )

    sim_ids = []
    for i, params in enumerate(param_scan):
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

        print(f"Simulating run {i} @ {params!r}\n")

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
