import numpy as np
from thesimulator.fleet_state import SlowSimpleFleetState
from thesimulator.data_structures import (
    Stop,
    InternalRequest,
    StopAction,
    PickupEvent,
    StopEvent,
    DeliveryEvent,
    TransportationRequest,
)
import operator as op
import itertools as it

from thesimulator.util.spaces import Euclidean

from tabulate import tabulate

"""
We will simulate a single taxi in euclidean space.
"""
n_busses = 1

"""
We define some transportation requests that will occur. We can either construct a list, or 
provide the requests in the form of a generator.
"""
request_origins = [np.array([np.cos(x), np.sin(x)]) for x in 2 * np.random.random(size=10)]
request_destinations = [np.array([0.1 * np.cos(x), 0.1 * np.sin(x)]) for x in 2 * np.random.random(size=10)]
request_times = np.linspace(0, 10, 10)
request_list = [
    TransportationRequest(request_id=i,
                          creation_timestamp=t,
                          origin=o,
                          destination=d,
                          pickup_timewindow_min=0,
                          pickup_timewindow_max=np.inf,
                          delivery_timewindow_min=0,
                          delivery_timewindow_max=np.inf)
    for i, (t, o, d) in enumerate(zip(request_times, request_origins, request_destinations))
]

request_generator = (r for r in request_list)


"""
Next we define the initial state of the system. In this case this means, our single taxi
starts empty at the point (0,0).
"""
initial_stoplists = {
        vehicle_id: [
            Stop(
                location=np.array([0,0]),
                request=InternalRequest(
                    request_id="CPE", creation_timestamp=0, location=np.array([0,0])
                ),
                action=StopAction.internal,
                estimated_arrival_time=0,
                time_window_min=0,
                time_window_max=np.inf,
            )
        ]
        for vehicle_id in range(n_busses)
    }

"""
We now initialize the FleetState using the initial stoplists, that is the initial position of our single taxi.
We could alternatively initialize the taxi with some previously planned stops.
"""
fs = SlowSimpleFleetState(initial_stoplists=initial_stoplists, space=Euclidean())

"""
Now we simulate the system using the request generator.
"""
events = list(fs.simulate(request_generator))


stop_events = sorted(
    filter(lambda x: isinstance(x, (PickupEvent, DeliveryEvent)), events),
    key=op.attrgetter("timestamp"),
)
vehicle_id_idxs = dict(
    zip(sorted(set(map(op.attrgetter("vehicle_id"), stop_events))), it.count(1))
)

output_list = [
    [None for _ in range(len(vehicle_id_idxs) + 1)] for _ in range(len(stop_events))
]

for row, event in zip(output_list, stop_events):
    row[0] = f"{event.timestamp:.2f}"
    row[
        vehicle_id_idxs[event.vehicle_id]
    ] = f"{'pu' if isinstance(event, PickupEvent) else 'do'} {event.request_id}"

print()
print(
    tabulate(
        output_list,
        headers=["time", *map(lambda x: f"v {x}", vehicle_id_idxs)],
        tablefmt="orgtbl",
    )
)