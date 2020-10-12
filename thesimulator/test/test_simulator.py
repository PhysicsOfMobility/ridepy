import pytest

import itertools as it
import collections as cl
import operator as op
import numpy as np

from tabulate import tabulate

from thesimulator.fleet_state import SlowSimpleFleetState, MPIFuturesFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    PickupEvent,
    StopEvent,
    DeliveryEvent,
)
from thesimulator.util.request_generators import RandomRequestGenerator
from thesimulator.util.spaces import Euclidean


def test_random_request_generator():
    rg = RandomRequestGenerator()
    reqs = list(it.islice(rg, 10))
    assert len(reqs) == 10
    assert all(
        reqs[i + 1].creation_timestamp > reqs[i].creation_timestamp for i in range(9)
    )
    for r in reqs:
        assert r.request_id is not None
        assert len(r.origin) == 2
        assert len(r.destination) == 2
        assert 0 <= r.origin[0] <= 1
        assert 0 <= r.origin[1] <= 1
        assert 0 <= r.destination[0] <= 1
        assert 0 <= r.destination[1] <= 1


@pytest.fixture
def initial_stoplists(request):
    n_buses = (
        request.node.get_closest_marker("n_buses").args[0]
        if request.node.get_closest_marker("n_buses") is not None
        else 10
    )

    return {
        vehicle_id: [
            Stop(
                location=(0, 0),
                vehicle_id=vehicle_id,
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=(0, 0)
                ),
                action=StopAction.internal,
                estimated_arrival_time=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ]
        for vehicle_id in range(n_buses)
    }


@pytest.mark.n_buses(10)
def test_slow_simple_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator(rate=10)
    reqs = list(it.islice(rg, 1000))
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs, t_cutoff=20))
    # print([event.vehicle_id for event in events if isinstance(event, PickupEvent)])
    # print("\n".join(map(str, events)))


@pytest.mark.n_buses(10)
def test_mpi_futures_fleet_state_simulate(initial_stoplists):
    rg = RandomRequestGenerator(rate=10)
    reqs = list(it.islice(rg, 1000))
    fs = MPIFuturesFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs, t_cutoff=20))
    # print([event.vehicle_id for event in events if isinstance(event, PickupEvent)])
    # print("\n".join(map(str, events)))


@pytest.mark.n_buses(10)
def test_with_taxicab_dispatcher_simple_1(initial_stoplists):
    rg = RandomRequestGenerator(rate=1)
    reqs = list(it.islice(rg, 180))
    fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())
    events = list(fs.simulate(reqs))

    stop_events = list(
        filter(lambda x: isinstance(x, (PickupEvent, DeliveryEvent)), events)
    )
    vehicle_id_idxs = dict(
        zip(set(map(op.attrgetter("vehicle_id"), stop_events)), it.count(1))
    )

    output_list = [
        [None for _ in range(len(vehicle_id_idxs) + 1)] for _ in range(len(stop_events))
    ]
    max_r_c = int(max(x.request_id for x in stop_events) // 10)

    for row, event in zip(output_list, stop_events):
        row[0] = f"{event.timestamp:.2f}"
        row[
            vehicle_id_idxs[event.vehicle_id]
        ] = f"{'pu' if isinstance(event, PickupEvent) else 'do'} {event.request_id}"  # f" {} {' '*int(max_r_c-event.request_id//10)}{event.request_id}"

    print(tabulate(output_list, headers=["Name", "Age"], tablefmt="orgtbl"))

    #
    # max_r_c = int(max(x.request_id for x in stop_events) // 10)
    # max_t_c = int(max(x.timestamp for x in stop_events) // 10)
    #
    # print(
    #     "|"
    #     + " " * (max_t_c + 1)
    #     + "t    "
    #     + "|"
    #     + "|".join(" v " + " "*(n_vehicles//10)+f"{n}" for n in range(n_vehicles))
    #     + "|"
    # )
    # for event in stop_events:
    #     ostring = (
    #         f"| {' '*int(max_t_c-event.timestamp//10)}{event.timestamp:.2f} |"
    #         + (" " * (max_r_c + 6) + "|") * event.vehicle_id
    #         + f" {'pu' if isinstance(event, PickupEvent) else 'do'} {' '*int(max_r_c-event.request_id//10)}{event.request_id} |"
    #         + (" " * (max_r_c + 6) + "|") * (n_vehicles - event.vehicle_id - 1)
    #     )
    #     print(ostring)
