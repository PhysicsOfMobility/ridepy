Writing a dispatcher
====================

General information
-------------------

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

Before starting to write your own dispatcher, it might prove helpful to have a look at the source code of the fairly trivial Python `.TaxicabDispatcherDriveFirst` dispatcher and possibly that of the Python `.BruteForceTotalTravelTimeMinimizingDispatcher` dispatcher to get some hints.

Python vs Cython/C++ dispatchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RidePy dispatchers may be written either in Python or in Cython/C++. The latter is recommended for performance-critical dispatchers. This guide will focus on Python dispatchers for now.

If you nonetheless want to have a look at the Cython/C++ dispatchers, you can find the currently implemented ones in the `ridepy.util.dispatchers_cython` module. There, the actual dispatching logic is implemented in ``cdispatchers.h``, which is exposed to Cython/Python by ``cdispatchers.pxd`` and ``cdispatchers.pyx``. In ``dispatchers.pyx`` and ``dispatchers.pxd``, an additional layer allows to set the `.LocType` appropriate for the `.TransportSpace` that is used. If this section confused you, please ignore it for now.

.. _dispatcherclass:

Function vs class dispatchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Strictly speaking, dispatchers in RidePy are not pure functions, but classes. This means, dispatchers can have state, such as the `.TransportSpace`'s `.LocType` for Cython/C++ dispatchers. This does not need to bother you at the moment, though, as there is a convenient wrapper for Python dispatchers that allows you to write them as pure functions. Just wrap your pure function dispatcher with the `.dispatcherclass` decorator from `.ridepy.util.dispatchers.dispatcher_class` like below, and you're good to go.


Signature of a Python dispatcher
--------------------------------

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

- ``MyDispatcher`` is a pure function decorated with `dispatcherclass`_, taking a `.TransportationRequest`, a `.Stoplist`, a `.TransportSpace` and an integer seat capacity
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

   DispatcherSolution = tuple[float, Stoplist, tuple[float, float, float, float]]
   """cost, updated_stoplist, (
       pickup_timewindow_min,
       pickup_timewindow_max,
       delivery_timewindow_min,
       delivery_timewindow_max,
   )
   """

- Here ``cost`` is the cost of insertion (float infinity if no solution is found), and the pick-up and delivery stop time window min and max values serve as the respective stops' constraints for upcoming insertions.

Logic
-----

The dispatcher is expected to implement the following logic:

- Check whether the request can be inserted into the given stoplist without violating any constraints, if so, where in the stoplist and at what cost.
- Create two `.Stop` objects for the pick-up and drop-off locations of the request, respectively, setting their appropriate

  - ``location`` (the location on the of the pick-up or drop-off on the `.TransportSpace`, e.g,. a 2D coordinate tuple or a network node ID. This may or may not be the same as the request's origin or destination)
  - ``request`` (the request object handled)
  - ``action`` (`.StopAction.pickup` or `.StopAction.dropoff`)
  - ``time_window_min`` (0 if not applicable)
  - ``time_window_max`` (float infinity if not applicable)

- Insert the two stops into the stoplist at the appropriate positions
- On all stops in the stoplist, including the two newly inserted ones, update the

  - ``estimated_arrival_time`` (by computing the travel times between the stops, starting from the first stop in the list (current position element CPE) and using the `.TransportSpace`'s `.t` method)
  - ``occupancy_after_servicing`` (the occupancy of the vehicle after the stop has been serviced. Currently, picking up a request takes up exactly one seat on the vehicle, but this may change in the future.)

- Finally, return

  - the cost of insertion (if no solution was found, return a cost of float infinity)
  - the updated, valid stoplist
  - the pick-up and delivery stop time window min and max values for the newly inserted stops

Using the dispatcher
--------------------

To use the dispatcher in simulations, just supply it to the `.FleetState` or `.SimulationSet` as you would with one of the dispatchers included with RidePy. Also, running tests on the dispatcher to ensure that it behaves as expected is highly recommended.