Writing a dispatcher
====================

General overview
----------------

Dispatchers are an essential part of RidePy: They determine the routes that the vehicles are going to take.

In essence, a dispatcher is a mapping of a new request and an existing stoplist associated with a single vehicle to an updated stoplist and a cost of inserting the request:

.. math::

   (\text{new request}, \text{stoplist})\mapsto(\text{cost}, \text{new stoplist})

The dispatcher is responsible for the following steps:

* Checking whether the pickup and dropoff stops for the new request may be inserted into the stoplist without violating any constraints.
* These constraints may entail:
  * Time window constraints of the request's pick-up and drop-off stops
  * Time window constraints of all other stops already in the stoplist
  * Vehicle seat capacity constraints
  * The trivial ridepooling constraint, i.e., the pick-up location needs to be visited before the drop-off location
* Multiple feasible solutions may exist. In this case, the dispatcher is expected to determine the solution ("insertion") incurring the minimum cost by some chose metric (the value of which is returned).
* It might happen that no solution can be found. In this case, the dispatcher must return a float :math:`\text{cost} = \infty` to let the caller know that the request can't be serviced by the vehicle in question.

It must be stressed that the dispatcher is solely responsible for checking the aforementioned constraints and for ensuring that the stoplists are kept in a valid state. This also means that the dispatcher must update the estimated arrival times of all stops except for the CPE (current position element)  which stores the current or last known location of the vehicle and is updated by `.VehicleState`. The dispatcher must not delete it, though.

The dispatcher is called on every vehicle's stoplist to determine the vehicle and route that incurs the least cost. If the minimum cost is infinite, i.e., the dispatcher has failed to return a finite cost of insertion for any of the vehicles, the rejection is *rejected*.

Before starting to write your own dispatcher, it might prove helpful to have a look at the source code of the trivial Python `.TaxicabDispatcherDriveFirst` and possibly that of the  Python `.BruteForceTotalTravelTimeMinimizingDispatcher` to get some hints.

Signature
---------

In the most simple case, a RidePy dispatcher is a Python function with the following signature:

.. code-block:: python

   @dispatcherclass
   def MyDispatcher(
       request: TransportationRequest,
       stoplist: Stoplist,
       space: TransportSpace,
       seat_capacity: int,
   ) -> DispatcherSolution: ...

Let's disect this:

- ``MyDispatcher`` is a pure function taking a `.TransportationRequest`, a `.Stoplist`, a `.TransportSpace` and an integer seat capacity
- A `.TransportationRequest` is defined like this:

.. code-block:: python

   ID = Union[str, int]
   """Generic ID, could be vehicle ID, request ID, ..."""


   @dataclass
   class Request:
       """
       A request for the system to perform a task
       """

       request_id: ID
       creation_timestamp: float


   @dataclass
   class TransportationRequest(Request):
       """
       A request for the system to perform a transportation task,
       through creating a route through the system given spatio-temporal constraints.
       """

       origin: Any
       destination: Any
       pickup_timewindow_min: float = 0
       pickup_timewindow_max: float = inf
       delivery_timewindow_min: float = 0
       delivery_timewindow_max: float = inf

- A `.Stoplist` is a list of `.Stop` objects:

.. code-block:: python

   Stoplist = List[Stop]
   """A list of `.Stop` objects. Specifies completely the current position and future
   actions a vehicle will make."""

- A `.Stop` in turn works like this:

.. code-block:: python

   class StopAction(Enum):
       """
       Representing actions that the system may perform at a specific location
       """

       pickup = 1
       dropoff = 2
       internal = 3


   @dataclass
   class Stop:
       """
       The notion of an action to be performed in fulfilling a request.
       Attached are spatio-temporal constraints.

       Parameters
       ----------
       location:
           location at which the stop is supposed to be serviced
       """

       location: Any
       request: Request
       action: StopAction
       estimated_arrival_time: float
       occupancy_after_servicing: int = 0
       time_window_min: float = 0
       time_window_max: float = inf

       @property
       def estimated_departure_time(self):
           return max(
               self.estimated_arrival_time,
               self.time_window_min,
           )

- Finally, the `.TransportSpace`:

.. code-block:: python

   class TransportSpace(ABC):
       @abstractmethod
       def d(self, u, v) -> Union[int, float]:
           """
           Return distance between points `u` and `v`.

           Parameters
           ----------
           u
               origin coordinate
           v
               destination coordinate

           Returns
           -------
           d
               distance
           """
           ...

       @abstractmethod
       def t(self, u, v) -> Union[int, float]:
           """
           Return travel time between points `u` and `v`.

           Parameters
           ----------
           u
               origin coordinate
           v
               destination coordinate

           Returns
           -------
           d
               travel time
           """

           ...

       @abstractmethod
       def random_point(self):
           """
           Return a random point on the space.

           Returns
           -------
               random point
           """
           ...

       @abstractmethod
       def interp_time(self, u, v, time_to_dest) -> Tuple[Any, Union[int, float]]:
           """
           Interpolate a location `x` between the origin `u` and the destination `v`
           as a function of the travel time between the unknown
           location and the destination `t(x, v) == time_to_dest`.

           Parameters
           ----------
           u
               origin coordinate
           v
               destination coordinate

           time_to_dest
               travel time from the unknown location `x` to the destination `v`

           Returns
           -------
           x
               interpolated coordinate of the unknown location `x`
           jump_dist
               remaining distance until the returned interpolated coordinate will be
               reached

           Note
           ----

           The notion of `jump_dist` is necessary in transport spaces whose locations
           are *discrete* (e.g. graphs). There if someone is travelling along a
           trajectory, at a certain time `t` one may be "in between" two locations `w`
           and `x`. Then the "position" at time `t` is ill defined, and we must settle
           for the fact that its location *will be* `x` at `t+jump_time`.
           """
           ...

       @abstractmethod
       def interp_dist(
           self, origin, destination, dist_to_dest
       ) -> Tuple[Any, Union[int, float]]:
           """
           Interpolate a location `x` between the origin `u` and the destination `v`
           as a function of the distance between the unknown
           location and the destination `d(x, v) == dist_to_dest`.

           Parameters
           ----------
           u
               origin coordinate
           v
               destination coordinate

           dist_to_dest
               distance from the unknown location `x` to the destination `v`

           Returns
           -------
           x
               interpolated coordinate of the unknown location `x`
           jump_dist
               remaining distance until the returned interpolated coordinate will be reached
           """
           ...

       @abstractmethod
       def asdict(self) -> dict: ...

       def __eq__(self, other: "TransportSpace"):
           return type(self) == type(other) and self.asdict() == other.asdict()

- From these inputs, the dispatcher determines the updated stoplist and cost of insertion.
- It then needs to returns a `.DispatcherSolution`, which is defined as follows:

.. code-block:: python

   DispatcherSolution = tuple[float, tuple[float, float, float, float]]
   """cost, (
       pickup_timewindow_min,
       pickup_timewindow_max,
       delivery_timewindow_min,
       delivery_timewindow_max,
   )
   """

- Here ``cost`` is the cost of insertion (float infinity if no solution is found), and the pick-up and delivery stop time window min and max values serve as the respective stops' constraints for upcoming insertions.

