# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Exploring [OR-tools](https://developers.google.com/optimization/routing/vrptw) for ridepooling

# + tags=[]
"""Vehicles Routing Problem (VRP) with Time Windows."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data["time_matrix"] = [
        [0, 6, 9, 8, 7, 3, 6, 2, 3, 2, 6, 6, 4, 4, 5, 9, 7],
        [6, 0, 8, 3, 2, 6, 8, 4, 8, 8, 13, 7, 5, 8, 12, 10, 14],
        [9, 8, 0, 11, 10, 6, 3, 9, 5, 8, 4, 15, 14, 13, 9, 18, 9],
        [8, 3, 11, 0, 1, 7, 10, 6, 10, 10, 14, 6, 7, 9, 14, 6, 16],
        [7, 2, 10, 1, 0, 6, 9, 4, 8, 9, 13, 4, 6, 8, 12, 8, 14],
        [3, 6, 6, 7, 6, 0, 2, 3, 2, 2, 7, 9, 7, 7, 6, 12, 8],
        [6, 8, 3, 10, 9, 2, 0, 6, 2, 5, 4, 12, 10, 10, 6, 15, 5],
        [2, 4, 9, 6, 4, 3, 6, 0, 4, 4, 8, 5, 4, 3, 7, 8, 10],
        [3, 8, 5, 10, 8, 2, 2, 4, 0, 3, 4, 9, 8, 7, 3, 13, 6],
        [2, 8, 8, 10, 9, 2, 5, 4, 3, 0, 4, 6, 5, 4, 3, 9, 5],
        [6, 13, 4, 14, 13, 7, 4, 8, 4, 4, 0, 10, 9, 8, 4, 13, 4],
        [6, 7, 15, 6, 4, 9, 12, 5, 9, 6, 10, 0, 1, 3, 7, 3, 10],
        [4, 5, 14, 7, 6, 7, 10, 4, 8, 5, 9, 1, 0, 2, 6, 4, 8],
        [4, 8, 13, 9, 8, 7, 10, 3, 7, 4, 8, 3, 2, 0, 4, 5, 6],
        [5, 12, 9, 14, 12, 6, 6, 7, 3, 3, 4, 7, 6, 4, 0, 9, 2],
        [9, 10, 18, 6, 8, 12, 15, 8, 13, 9, 13, 3, 4, 5, 9, 0, 9],
        [7, 14, 9, 16, 14, 8, 5, 10, 6, 5, 4, 10, 8, 6, 2, 9, 0],
    ]
    data["time_windows"] = [
        (0, 5),  # depot
        (7, 12),  # 1
        (10, 15),  # 2
        (16, 18),  # 3
        (10, 13),  # 4
        (0, 5),  # 5
        (5, 10),  # 6
        (0, 4),  # 7
        (5, 10),  # 8
        (0, 3),  # 9
        (10, 16),  # 10
        (10, 15),  # 11
        (0, 5),  # 12
        (5, 10),  # 13
        (7, 8),  # 14
        (10, 15),  # 15
        (11, 15),  # 16
    ]
    data["num_vehicles"] = 4
    data["depot"] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} Time({1},{2}) -> ".format(
                manager.IndexToNode(index),
                solution.Min(time_var),
                solution.Max(time_var),
            )
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Time({1},{2})\n".format(
            manager.IndexToNode(index), solution.Min(time_var), solution.Max(time_var)
        )
        plan_output += "Time of the route: {}min\n".format(solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print("Total time of all routes: {}min".format(total_time))


"""Solve the VRP with time windows."""
# Instantiate the data problem.
data = create_data_model()

# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(
    len(data["time_matrix"]), data["num_vehicles"], data["depot"]
)

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)


# Create and register a transit callback.
def time_callback(from_index, to_index):
    """Returns the travel time between the two nodes."""
    # Convert from routing variable Index to time matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data["time_matrix"][from_node][to_node]


transit_callback_index = routing.RegisterTransitCallback(time_callback)

# Define cost of each arc.
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Add Time Windows constraint.
time = "Time"
routing.AddDimension(
    transit_callback_index,
    30,  # allow waiting time
    30,  # maximum time per vehicle
    False,  # Don't force start cumul to zero.
    time,
)
time_dimension = routing.GetDimensionOrDie(time)
# Add time window constraints for each location except depot.
for location_idx, time_window in enumerate(data["time_windows"]):
    if location_idx == data["depot"]:
        continue
    index = manager.NodeToIndex(location_idx)
    time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
# Add time window constraints for each vehicle start node.
depot_idx = data["depot"]
for vehicle_id in range(data["num_vehicles"]):
    index = routing.Start(vehicle_id)
    time_dimension.CumulVar(index).SetRange(
        data["time_windows"][depot_idx][0], data["time_windows"][depot_idx][1]
    )

# Instantiate route start and end times to produce feasible times.
for i in range(data["num_vehicles"]):
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.Start(i)))
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

# Solve the problem.
solution = routing.SolveWithParameters(search_parameters)

# Print solution on console.
if solution:
    print_solution(data, manager, routing, solution)

# -

# ## Great! The stuff works, let's now adapt it for our use case

# + tags=[]
from thesimulator.data_structures import (
    TransportationRequest,
    InternalRequest,
    Stop,
    StopAction,
)
from thesimulator.util.spaces import Manhattan2D
from numpy import inf

# ortools doesn't understand infinity
inf = 10000
# -

# ### Set up two vehicles and their stoplists

# + tags=[]
manhattan = Manhattan2D()

request_1 = TransportationRequest(
    request_id=1,
    creation_timestamp=0,
    origin=(2, 100),
    destination=(10, 100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
request_2 = TransportationRequest(
    request_id=2,
    creation_timestamp=0,
    origin=(2, -100),
    destination=(10, -100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)

requests = [request_1, request_2]

stoplist_vehicle_1 = [
    Stop(
        location=(0, 100),
        request=InternalRequest(request_id=-1, creation_timestamp=0, location=(0, 100)),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=request_1.origin,
        request=request_1,
        action=StopAction.pickup,
        estimated_arrival_time=2,
        occupancy_after_servicing=1,
        time_window_min=request_1.pickup_timewindow_min,
        time_window_max=request_1.pickup_timewindow_max,
    ),
    Stop(
        location=request_1.destination,
        request=request_1,
        action=StopAction.dropoff,
        estimated_arrival_time=10,
        occupancy_after_servicing=0,
        time_window_min=request_1.delivery_timewindow_min,
        time_window_max=request_1.delivery_timewindow_max,
    ),
]


stoplist_vehicle_2 = [
    Stop(
        location=(0, -100),
        request=InternalRequest(
            request_id=-1, creation_timestamp=0, location=(0, -100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=request_2.origin,
        request=request_2,
        action=StopAction.pickup,
        estimated_arrival_time=2,
        occupancy_after_servicing=1,
        time_window_min=request_2.pickup_timewindow_min,
        time_window_max=request_2.pickup_timewindow_max,
    ),
    Stop(
        location=request_2.destination,
        request=request_2,
        action=StopAction.dropoff,
        estimated_arrival_time=10,
        occupancy_after_servicing=0,
        time_window_min=request_2.delivery_timewindow_min,
        time_window_max=request_2.delivery_timewindow_max,
    ),
]

stoplists = [stoplist_vehicle_1, stoplist_vehicle_2]
# -

# ### A new request...

# + tags=[]
new_request = TransportationRequest(
    request_id=99,
    creation_timestamp=0,
    origin=(5, 80),
    destination=(9, 80),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
requests.append(new_request)
# -

# #### massage the ridepy data structures to a more or-tools friendly format

# + tags=[]
all_stops = [stop for stoplist in stoplists for stop in stoplist]

stops_for_new_request = [
    Stop(
        location=new_request.origin,
        request=new_request,
        action=StopAction.pickup,
        estimated_arrival_time=None,
        occupancy_after_servicing=None,
        time_window_min=new_request.pickup_timewindow_min,
        time_window_max=new_request.pickup_timewindow_max,
    ),
    Stop(
        location=new_request.destination,
        request=new_request,
        action=StopAction.dropoff,
        estimated_arrival_time=None,
        occupancy_after_servicing=None,
        time_window_min=new_request.delivery_timewindow_min,
        time_window_max=new_request.delivery_timewindow_max,
    ),
]

all_stops.extend(stops_for_new_request)

dummy_end_stops = [
    Stop(
        location=(1000, 100),
        request=InternalRequest(
            request_id=1000, creation_timestamp=0, location=(1000, 100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=(1000, -100),
        request=InternalRequest(
            request_id=2000, creation_timestamp=0, location=(1000, -100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
]

# TODO: Have to add the "stops" for the new request too

all_stops.extend(dummy_end_stops)

stoploc2idx = {stop.location: idx for idx, stop in enumerate(all_stops)}
start_loc_idxs = [
    stoploc2idx[stoplist_vehicle_1[0].location],
    stoploc2idx[stoplist_vehicle_2[0].location],
]
end_loc_idxs = [stoploc2idx[end_stop.location] for end_stop in dummy_end_stops]


pickup_delivery_idx_pairs = []
for request in requests:
    for stop_idx, stop in enumerate(all_stops):
        if stop.request == request:
            if stop.action == StopAction.pickup:
                pu_idx = stop_idx
            if stop.action == StopAction.dropoff:
                do_idx = stop_idx
    pickup_delivery_idx_pairs.append((pu_idx, do_idx))

delta_occupancies = [
    {StopAction.pickup: 1, StopAction.dropoff: -1, StopAction.internal: 0}[stop.action]
    for stop in all_stops
]
# -

all_stops

# + tags=[]
pickup_delivery_idx_pairs
# -

# #### Start setting up the ortools problem

# + tags=[]
"""Solve the VRP with time windows."""
# Instantiate the data problem.
num_vehicles = len(stoplists)

# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(
    len(all_stops), num_vehicles, start_loc_idxs, end_loc_idxs
)

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)

# Create and register a transit callback.
def time_callback(from_index, to_index):
    """Returns the travel time between the two nodes."""
    # Convert from routing variable Index to time matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)

    # if either from_index or the to_index is a dummy end node, return 0
    if from_index in end_loc_idxs or to_index in end_loc_idxs:
        return 0
    else:
        from_loc = all_stops[from_index].location
        to_loc = all_stops[to_index].location
        return manhattan.d(from_loc, to_loc)


transit_callback_index = routing.RegisterTransitCallback(time_callback)

# Define cost of each arc.
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Add Time Windows constraint.
time = "Time"
routing.AddDimension(
    evaluator_index=transit_callback_index,
    slack_max=1000000,  # allow waiting time. TODO set to what is sensible
    capacity=10000000,  # maximum time per vehicle. TODO set to what is sensible
    fix_start_cumul_to_zero=True,  # force start cumul to zero
    name=time,
)
time_dimension = routing.GetDimensionOrDie(time)

# Add time window constraints for each location except depot.
# https://developers.google.com/optimization/routing/vrptw
for stop_idx, stop in enumerate(all_stops):
    if stop_idx not in start_loc_idxs and stop_idx not in end_loc_idxs:
        index = manager.NodeToIndex(stop_idx)
        t_min, t_max = stop.time_window_min, stop.time_window_max

        time_dimension.CumulVar(index).SetRange(t_min, t_max)

# Add time window constraints for each vehicle's start node
for vehicle_idx in range(num_vehicles):
    start_stop = all_stops[start_loc_idxs[vehicle_idx]]
    index = routing.Start(vehicle_idx)
    time_dimension.CumulVar(index).SetRange(
        start_stop.time_window_min, start_stop.time_window_max
    )

# TODO: onboard customers have to be dropped off by the same vehicle
# - Add a single capacity dimension for each onboard trip.
# - The value is 0 everywhere. 1 for the dropoff.
# - the capacity constraint is set at 1.
# - Initial value is -1 for the vehicle carrying the load, 0 for everyone else.
# https://developers.google.com/optimization/routing/pickup_delivery
# OR: PreAssignment
# OR: SetAllowedVehiclesForIndex (seems cleanest)

# Define Transportation Requests: i.e. add the notion of pickups and deliveries
for pu_stop_idx, do_stop_idx in pickup_delivery_idx_pairs:
    pickup_index = manager.NodeToIndex(pu_stop_idx)
    delivery_index = manager.NodeToIndex(do_stop_idx)
    routing.AddPickupAndDelivery(pickup_index, delivery_index)
    routing.solver().Add(
        routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
    )
    routing.solver().Add(
        time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index)
    )

# add capacity constraints


def delta_occupancy_callback(from_index):
    """Returns the demand of the node."""
    # Convert from routing variable Index to demands NodeIndex.
    from_node = manager.IndexToNode(from_index)
    return delta_occupancies[from_node]


delta_occupancy_callback_index = routing.RegisterUnaryTransitCallback(
    delta_occupancy_callback
)

routing.AddDimensionWithVehicleCapacity(
    delta_occupancy_callback_index,
    0,  # null capacity slack
    [4] * num_vehicles,  # vehicle maximum capacities
    True,  # start cumul to zero
    "Capacity",
)

# Instantiate route start and end times to produce feasible times.
for i in range(num_vehicles):
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.Start(i)))
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

# Solve the problem.
solution = routing.SolveWithParameters(search_parameters)
solution


# + tags=[]
def print_solution(stops, num_vehicles, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} Time({1},{2}) -> ".format(
                stops[manager.IndexToNode(index)].location,
                solution.Min(time_var),
                solution.Max(time_var),
            )
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Time({1},{2})\n".format(
            stops[manager.IndexToNode(index)].location,
            solution.Min(time_var),
            solution.Max(time_var),
        )
        plan_output += "Time of the route: {}min\n".format(solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print("Total time of all routes: {}min".format(total_time))


# + tags=[]
# Print solution on console.
if solution:
    print_solution(all_stops, num_vehicles, manager, routing, solution)
# -

# ## So it spews out sensible output. Wrap it into a function and check various edge cases

# + tags=[]
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from thesimulator.data_structures import (
    TransportationRequest,
    InternalRequest,
    Stop,
    StopAction,
)
from thesimulator.util.spaces import Manhattan2D
from numpy import inf

# ortools doesn't understand infinity
inf = 10000

manhattan = Manhattan2D()


def create_data(request_1, request_2, new_request, vehicle_capacities=None):
    if vehicle_capacities is None:
        vehicle_capacities = [10, 10]
    requests = [request_1, request_2]

    stoplist_vehicle_1 = [
        Stop(
            location=(0, 100),
            request=InternalRequest(
                request_id=-1, creation_timestamp=0, location=(0, 100)
            ),
            action=StopAction.internal,
            estimated_arrival_time=0,
            occupancy_after_servicing=0,
            time_window_min=0,
            time_window_max=inf,
        ),
        Stop(
            location=request_1.origin,
            request=request_1,
            action=StopAction.pickup,
            estimated_arrival_time=2,
            occupancy_after_servicing=1,
            time_window_min=request_1.pickup_timewindow_min,
            time_window_max=request_1.pickup_timewindow_max,
        ),
        Stop(
            location=request_1.destination,
            request=request_1,
            action=StopAction.dropoff,
            estimated_arrival_time=10,
            occupancy_after_servicing=0,
            time_window_min=request_1.delivery_timewindow_min,
            time_window_max=request_1.delivery_timewindow_max,
        ),
    ]

    stoplist_vehicle_2 = [
        Stop(
            location=(0, -100),
            request=InternalRequest(
                request_id=-1, creation_timestamp=0, location=(0, -100)
            ),
            action=StopAction.internal,
            estimated_arrival_time=0,
            occupancy_after_servicing=0,
            time_window_min=0,
            time_window_max=inf,
        ),
        Stop(
            location=request_2.origin,
            request=request_2,
            action=StopAction.pickup,
            estimated_arrival_time=2,
            occupancy_after_servicing=1,
            time_window_min=request_2.pickup_timewindow_min,
            time_window_max=request_2.pickup_timewindow_max,
        ),
        Stop(
            location=request_2.destination,
            request=request_2,
            action=StopAction.dropoff,
            estimated_arrival_time=10,
            occupancy_after_servicing=0,
            time_window_min=request_2.delivery_timewindow_min,
            time_window_max=request_2.delivery_timewindow_max,
        ),
    ]

    stoplists = [stoplist_vehicle_1, stoplist_vehicle_2]

    requests.append(new_request)

    all_stops = [stop for stoplist in stoplists for stop in stoplist]

    stops_for_new_request = [
        Stop(
            location=new_request.origin,
            request=new_request,
            action=StopAction.pickup,
            estimated_arrival_time=None,
            occupancy_after_servicing=None,
            time_window_min=new_request.pickup_timewindow_min,
            time_window_max=new_request.pickup_timewindow_max,
        ),
        Stop(
            location=new_request.destination,
            request=new_request,
            action=StopAction.dropoff,
            estimated_arrival_time=None,
            occupancy_after_servicing=None,
            time_window_min=new_request.delivery_timewindow_min,
            time_window_max=new_request.delivery_timewindow_max,
        ),
    ]

    all_stops.extend(stops_for_new_request)

    dummy_end_stops = [
        Stop(
            location=(1000, 100),
            request=InternalRequest(
                request_id=1000, creation_timestamp=0, location=(1000, 100)
            ),
            action=StopAction.internal,
            estimated_arrival_time=0,
            occupancy_after_servicing=0,
            time_window_min=0,
            time_window_max=inf,
        ),
        Stop(
            location=(1000, -100),
            request=InternalRequest(
                request_id=2000, creation_timestamp=0, location=(1000, -100)
            ),
            action=StopAction.internal,
            estimated_arrival_time=0,
            occupancy_after_servicing=0,
            time_window_min=0,
            time_window_max=inf,
        ),
    ]

    # TODO: Have to add the "stops" for the new request too

    all_stops.extend(dummy_end_stops)

    stoploc2idx = {stop.location: idx for idx, stop in enumerate(all_stops)}
    start_loc_idxs = [
        stoploc2idx[stoplist_vehicle_1[0].location],
        stoploc2idx[stoplist_vehicle_2[0].location],
    ]
    end_loc_idxs = [stoploc2idx[end_stop.location] for end_stop in dummy_end_stops]

    pickup_delivery_idx_pairs = []
    for request in requests:
        for stop_idx, stop in enumerate(all_stops):
            if stop.request == request:
                if stop.action == StopAction.pickup:
                    pu_idx = stop_idx
                if stop.action == StopAction.dropoff:
                    do_idx = stop_idx
        pickup_delivery_idx_pairs.append((pu_idx, do_idx))

    delta_occupancies = [
        {StopAction.pickup: 1, StopAction.dropoff: -1, StopAction.internal: 0}[
            stop.action
        ]
        for stop in all_stops
    ]

    return dict(
        num_vehicles=len(stoplists),
        stops=all_stops,
        start_loc_idxs=start_loc_idxs,
        end_loc_idxs=end_loc_idxs,
        vehicle_capacities=vehicle_capacities,
        pickup_delivery_idx_pairs=pickup_delivery_idx_pairs,
    )


def print_solution(stops, num_vehicles, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} -> ".format(stops[manager.IndexToNode(index)].location)
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0}\n".format(stops[manager.IndexToNode(index)].location)
        plan_output += "Time of the route: {}min\n".format(solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print("Total time of all routes: {}min".format(total_time))


def solve_vrp(data):
    """Solve the VRP with time windows."""
    # Instantiate the data problem.
    num_vehicles = data["num_vehicles"]
    all_stops = data["stops"]
    start_loc_idxs = data["start_loc_idxs"]
    end_loc_idxs = data["end_loc_idxs"]
    vehicle_capacities = data["vehicle_capacities"]
    pickup_delivery_idx_pairs = data["pickup_delivery_idx_pairs"]

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(all_stops), num_vehicles, start_loc_idxs, end_loc_idxs
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        # if either from_index or the to_index is a dummy end node, return 0
        if from_index in end_loc_idxs or to_index in end_loc_idxs:
            return 0
        else:
            from_loc = all_stops[from_index].location
            to_loc = all_stops[to_index].location
            return manhattan.d(from_loc, to_loc)

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    time = "Time"
    routing.AddDimension(
        evaluator_index=transit_callback_index,
        slack_max=1000000,  # allow waiting time. TODO set to what is sensible
        capacity=10000000,  # maximum time per vehicle. TODO set to what is sensible
        fix_start_cumul_to_zero=True,  # force start cumul to zero
        name=time,
    )
    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot.
    # https://developers.google.com/optimization/routing/vrptw
    for stop_idx, stop in enumerate(all_stops):
        if stop_idx not in start_loc_idxs and stop_idx not in end_loc_idxs:
            index = manager.NodeToIndex(stop_idx)
            t_min, t_max = stop.time_window_min, stop.time_window_max

            time_dimension.CumulVar(index).SetRange(t_min, t_max)

    # Add time window constraints for each vehicle's start node
    for vehicle_idx in range(num_vehicles):
        start_stop = all_stops[start_loc_idxs[vehicle_idx]]
        index = routing.Start(vehicle_idx)
        time_dimension.CumulVar(index).SetRange(
            start_stop.time_window_min, start_stop.time_window_max
        )

    # Define Transportation Requests: i.e. add the notion of pickups and deliveries
    for pu_stop_idx, do_stop_idx in pickup_delivery_idx_pairs:
        pickup_index = manager.NodeToIndex(pu_stop_idx)
        delivery_index = manager.NodeToIndex(do_stop_idx)
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
        )
        routing.solver().Add(
            time_dimension.CumulVar(pickup_index)
            <= time_dimension.CumulVar(delivery_index)
        )

    # add capacity constraints

    def delta_occupancy_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return delta_occupancies[from_node]

    delta_occupancy_callback_index = routing.RegisterUnaryTransitCallback(
        delta_occupancy_callback
    )

    routing.AddDimensionWithVehicleCapacity(
        delta_occupancy_callback_index,
        0,  # null capacity slack
        vehicle_capacities,  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Instantiate route start and end times to produce feasible times.
    for i in range(num_vehicles):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    print_solution(all_stops, num_vehicles, manager, routing, solution)


# + tags=[]
manhattan = Manhattan2D()

request_1 = TransportationRequest(
    request_id=1,
    creation_timestamp=0,
    origin=(2, 100),
    destination=(10, 100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
request_2 = TransportationRequest(
    request_id=2,
    creation_timestamp=0,
    origin=(2, -100),
    destination=(10, -100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
new_request = TransportationRequest(
    request_id=99,
    creation_timestamp=0,
    origin=(5, -80),
    destination=(9, -80),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)


data = create_data(request_1, request_2, new_request, vehicle_capacities=[10, 1])
solve_vrp(data)
# -

# ## Last step before this can actually be used: Take care of onboard requests

# + tags=[]
manhattan = Manhattan2D()

request_1 = TransportationRequest(
    request_id=1,
    creation_timestamp=0,
    origin=(2, 100),
    destination=(10, 100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
request_2 = TransportationRequest(
    request_id=2,
    creation_timestamp=0,
    origin=(2, -100),
    destination=(10, -100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)

onb_request_1 = TransportationRequest(
    request_id=11,
    creation_timestamp=0,
    origin=(-10, -100),
    destination=(5, -100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
onb_request_2 = TransportationRequest(
    request_id=222,
    creation_timestamp=0,
    origin=(-10, 100),
    destination=(5, 100),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)

onb_requests = [[onb_request_1], [onb_request_2]]

requests = [request_1, request_2]

stoplist_vehicle_1 = [
    Stop(
        location=(0, 100),
        request=InternalRequest(request_id=-1, creation_timestamp=0, location=(0, 100)),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=onb_request_1.destination,
        request=onb_request_1,
        action=StopAction.dropoff,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=request_1.origin,
        request=request_1,
        action=StopAction.pickup,
        estimated_arrival_time=2,
        occupancy_after_servicing=1,
        time_window_min=request_1.pickup_timewindow_min,
        time_window_max=request_1.pickup_timewindow_max,
    ),
    Stop(
        location=request_1.destination,
        request=request_1,
        action=StopAction.dropoff,
        estimated_arrival_time=10,
        occupancy_after_servicing=0,
        time_window_min=request_1.delivery_timewindow_min,
        time_window_max=request_1.delivery_timewindow_max,
    ),
]


stoplist_vehicle_2 = [
    Stop(
        location=(0, -100),
        request=InternalRequest(
            request_id=-1, creation_timestamp=0, location=(0, -100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=onb_request_2.destination,
        request=onb_request_2,
        action=StopAction.dropoff,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=request_2.origin,
        request=request_2,
        action=StopAction.pickup,
        estimated_arrival_time=2,
        occupancy_after_servicing=1,
        time_window_min=request_2.pickup_timewindow_min,
        time_window_max=request_2.pickup_timewindow_max,
    ),
    Stop(
        location=request_2.destination,
        request=request_2,
        action=StopAction.dropoff,
        estimated_arrival_time=10,
        occupancy_after_servicing=0,
        time_window_min=request_2.delivery_timewindow_min,
        time_window_max=request_2.delivery_timewindow_max,
    ),
]

stoplists = [stoplist_vehicle_1, stoplist_vehicle_2]

new_request = TransportationRequest(
    request_id=99,
    creation_timestamp=0,
    origin=(5, 80),
    destination=(9, 80),
    pickup_timewindow_min=0,
    pickup_timewindow_max=inf,
    delivery_timewindow_min=0,
    delivery_timewindow_max=inf,
)
requests.append(new_request)

all_stops = [stop for stoplist in stoplists for stop in stoplist]

stops_for_new_request = [
    Stop(
        location=new_request.origin,
        request=new_request,
        action=StopAction.pickup,
        estimated_arrival_time=None,
        occupancy_after_servicing=None,
        time_window_min=new_request.pickup_timewindow_min,
        time_window_max=new_request.pickup_timewindow_max,
    ),
    Stop(
        location=new_request.destination,
        request=new_request,
        action=StopAction.dropoff,
        estimated_arrival_time=None,
        occupancy_after_servicing=None,
        time_window_min=new_request.delivery_timewindow_min,
        time_window_max=new_request.delivery_timewindow_max,
    ),
]

all_stops.extend(stops_for_new_request)

dummy_end_stops = [
    Stop(
        location=(1000, 100),
        request=InternalRequest(
            request_id=1000, creation_timestamp=0, location=(1000, 100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
    Stop(
        location=(1000, -100),
        request=InternalRequest(
            request_id=2000, creation_timestamp=0, location=(1000, -100)
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=inf,
    ),
]


all_stops.extend(dummy_end_stops)

stoploc2idx = {stop.location: idx for idx, stop in enumerate(all_stops)}
start_loc_idxs = [
    stoploc2idx[stoplist_vehicle_1[0].location],
    stoploc2idx[stoplist_vehicle_2[0].location],
]
end_loc_idxs = [stoploc2idx[end_stop.location] for end_stop in dummy_end_stops]

onboard_requests_delivery_stop_idxs = [list() for _ in stoplists]
for vehicle_idx, onb_requests_single_vehicle in enumerate(onb_requests):
    for stop_idx, stop in enumerate(all_stops):
        if stop.request in onb_requests_single_vehicle:
            onboard_requests_delivery_stop_idxs[vehicle_idx].append(stop_idx)


pickup_delivery_idx_pairs = []
for request in requests:
    for stop_idx, stop in enumerate(all_stops):
        if stop.request == request:
            if stop.action == StopAction.pickup:
                pu_idx = stop_idx
            if stop.action == StopAction.dropoff:
                do_idx = stop_idx
    pickup_delivery_idx_pairs.append((pu_idx, do_idx))

delta_occupancies = [
    {StopAction.pickup: 1, StopAction.dropoff: -1, StopAction.internal: 0}[stop.action]
    for stop in all_stops
]

for vehicle_idx, stop_idx in enumerate(start_loc_idxs):
    delta_occupancies[stop_idx] = len(
        onboard_requests_delivery_stop_idxs[vehicle_idx]
    )  # hack: Assign the delta_occupancy=num_onboard at CPE
delta_occupancies
# -

# ### Set up the ortools problem

# + tags=[]
"""Solve the VRP with time windows."""
# Instantiate the data problem.
num_vehicles = len(stoplists)

# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(
    len(all_stops), num_vehicles, start_loc_idxs, end_loc_idxs
)

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)

# Create and register a transit callback.
def time_callback(from_index, to_index):
    """Returns the travel time between the two nodes."""
    # Convert from routing variable Index to time matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)

    # if either from_index or the to_index is a dummy end node, return 0
    if from_index in end_loc_idxs or to_index in end_loc_idxs:
        return 0
    else:
        from_loc = all_stops[from_index].location
        to_loc = all_stops[to_index].location
        return manhattan.d(from_loc, to_loc)


transit_callback_index = routing.RegisterTransitCallback(time_callback)

# Define cost of each arc.
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Add Time Windows constraint.
time = "Time"
routing.AddDimension(
    evaluator_index=transit_callback_index,
    slack_max=1000000,  # allow waiting time. TODO set to what is sensible
    capacity=10000000,  # maximum time per vehicle. TODO set to what is sensible
    fix_start_cumul_to_zero=True,  # force start cumul to zero
    name=time,
)
time_dimension = routing.GetDimensionOrDie(time)

# Add time window constraints for each location except depot.
# https://developers.google.com/optimization/routing/vrptw
for stop_idx, stop in enumerate(all_stops):
    if stop_idx not in start_loc_idxs and stop_idx not in end_loc_idxs:
        index = manager.NodeToIndex(stop_idx)
        t_min, t_max = stop.time_window_min, stop.time_window_max

        time_dimension.CumulVar(index).SetRange(t_min, t_max)

# Add time window constraints for each vehicle's start node
for vehicle_idx in range(num_vehicles):
    start_stop = all_stops[start_loc_idxs[vehicle_idx]]
    index = routing.Start(vehicle_idx)
    time_dimension.CumulVar(index).SetRange(
        start_stop.time_window_min, start_stop.time_window_max
    )

# Ensure onboard requests are delivered by the respective vehicle
for vehicle_idx, stop_idxs in enumerate(onboard_requests_delivery_stop_idxs):
    for stop_idx in stop_idxs:
        print(f"Trying to get vehicle #{vehicle_idx} to service stop #{stop_idx}")
        index = manager.NodeToIndex(stop_idx)
        routing.SetAllowedVehiclesForIndex([vehicle_idx], index)


# Define Transportation Requests: i.e. add the notion of pickups and deliveries
for pu_stop_idx, do_stop_idx in pickup_delivery_idx_pairs:
    pickup_index = manager.NodeToIndex(pu_stop_idx)
    delivery_index = manager.NodeToIndex(do_stop_idx)
    routing.AddPickupAndDelivery(pickup_index, delivery_index)
    routing.solver().Add(
        routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
    )
    routing.solver().Add(
        time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index)
    )

# add capacity constraints
def delta_occupancy_callback(from_index):
    """Returns the demand of the node."""
    # Convert from routing variable Index to demands NodeIndex.
    from_node = manager.IndexToNode(from_index)
    return delta_occupancies[from_node]


delta_occupancy_callback_index = routing.RegisterUnaryTransitCallback(
    delta_occupancy_callback
)

routing.AddDimensionWithVehicleCapacity(
    delta_occupancy_callback_index,
    0,  # null capacity slack
    [1] * num_vehicles,  # vehicle maximum capacities
    True,  # start cumul to zero
    "Capacity",
)

# Instantiate route start and end times to produce feasible times.
for i in range(num_vehicles):
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.Start(i)))
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))

# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)

# Solve the problem.
solution = routing.SolveWithParameters(search_parameters)

if solution:
    print_solution(all_stops, num_vehicles, manager, routing, solution)
# -

# ## Features tested to be working (backed up)
# * Capacity constraints with onboard.
#
# links: https://github.com/google/or-tools/issues/1672
