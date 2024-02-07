Introduction
============

RidePy lets a user specify a `.FleetState` of :math:`n` vehicles with desired
passenger capacities, as well as an ``iterator`` of `.TransportationRequest`
objects, each containing:


* ``request_id``
* ``creation_timestamp``
* ``origin``
* ``destination``
* ``pickup_timewindow_min``
* ``pickup_timewindow_max``
* ``delivery_timewindow_min``
* ``delivery_timewindow_max``

The request iterator must yield requests in increasing order of ``creation_timestamp``. 


Calling `.FleetState.simulate()` then executes the simulation, which outputs a
sequence of `Event` objects (add link here), from which the user can compute various metrics,
optionally using the :mod:`.util.analytics` module. 


.. _desc_stoplist:

The stoplist
------------
`.FleetState` contains a dictionary `.fleet`, which maps a ``vehicle_id`` to a
`.VehicleState`. A `VehicleState`, in turn holds the future trajectory of the
vehicle in the form of a `~.vehicleState.Stoplist`: a list of `.Stop` objects containing:

* ``location``,
* ``request`` to be serviced, 
* ``action``: one of `pickup`, `dropoff` or `internal`, 
* ``estimated_arrival_time``,
* ``occupancy_after_servicing``,
* ``time_window_min``,
* ``time_window_max``.

Therefore, a `Stoplist` contains all the information on where the vehicle will
go and what it will do in the future (if the stoplist does not change in the
meantime, by e.g. a `.dispatcher` inserting a new `TransportationRequest` s
pickup and dropoff in it).


.. _desc_cpestop:

The CPE Stop
~~~~~~~~~~~~
The first element of any vehicle's `Stoplist` is a `Stop`  object that is
called the "CPE stop" (*current position element*), signifying the immediate
position of the vehicle. It is not associated with any `TransportationRequest`.
The ``estimated_arrival_time`` of this stop defines the time at which the
vehicle is at the CPEs location. This is always roughly the *current* location
and time, though it might be immediate past (before it has been updated to the
current state) or immediate future (when the vehicle is in between two adjacent nodes
on a graph, see `.TransportSpace.interp_time`).




The Simulation run: advancing the internal clock
-------------------------------------------------

When a `.FleetState` is created, an internal "clock" is started at time :math:`t= 0`.
When the simulation is run,

1. The next request ``r`` is fetched from the request iterator. 
2. The simulator's internal clock is advanced to the ``creation_timestamp`` of
   ``r``. For each vehicle

   - All the stops whose ``estimated_arrival_time`` is less than the current
     timestamp is removed. For each of these stops an appropriate `PickupEvent`
     or `DeliveryEvent` is emitted.
   - Based on its ``Stoplist``, its "current" position is inferred, and the
     ``location`` and ``estimated_arrival_time`` of its CPE stop are modified
     accordingly.
3. The vehicle that is "best suited" for transporting ``r`` is determined by
   the `dispatcher`, and two new stops are inserted into its `Stoplist`: the
   pickup and dropoff of ``r``. We describe below how this choice is made. A
   `.RequestAcceptanceEvent` is emitted. If no such vehicle is found, a
   `.RequestRejectionEvent` is emitted instead. 
4. The previous steps are repeated until either the request iterator is
   exhausted or a time cutoff is reached.

.. _desc_dispatcher:

The dispatcher
--------------
The dispatcher determines which vehicle should service a certain request, and
in which order it should service the requests assigned to it. ridepy
defines a clean interface enabling the users to create their own dispatchers. A
number of predefined ones are available in `.util.dispatchers`.

When a new `TransportationRequest` needs to be processed: 

1. The ``dispatcher`` is called for each vehicle, which can be thought of as
   the mapping `(new_request, stoplist) ⇒ (cost, new_stoplist)`. It

  + Checks if the pickup and dropoff of ``r`` can be inserted to the
    vehicle's ``Stoplist`` without violating

    * The new request's ``pickup_timewindow_min|max`` and
      ``delivery_timewindow_min|max``. 
    * The ``time_window_min|max`` of every existing stop in the stoplist of
      the vehicle.
    * The capacity contraints of the vehicle.
    * The implicit constraint of inserting Pickup, with regards to order,
      *before* Dropoff

  + There can be multiple possible insertions that do not violate any of
    these constraints. The dispatcher computes a numerical *cost* for each
    possible insertion and chooses the insertion with the least cost. One
    such cost could be the total detour caused by an insertion, for example. 
  + If *no* insertion is found for a vehicle, the dispatcher returns a cost
    of :math:`\infty`. 
2. If more than one vehicle can service the request, then the one with minimum
   cost is chosen. That is, its ``Stoplist`` is changed to the ``new_stoplist``
   returned by the dispatcher.

The dispatcher is solely responsible for keeping the stoplist in a internally
valid state, as the one with minimal cost substitutes the original one for the
respective vehicle. Constraints are not checked again elsewhere. This
incorporates in particular estimated arrival times which are constrained by the
travel time on the transport space.


.. _desc_space:

The Transport Space
-------------------
The transport space defines the space that stops and requests live on. This has
primarily three implications:

1. It defines the coordinates used for specifying locations. This can e.g. be
   an integer number for graph vertices, or a pair of floats for a continuous
   two-dimensional space.
2. The first key function that the `.TransportSpace` provides is a metric
   :math:`T\times T\rightarrow\mathbb R, (u,v)\mapsto d(u,v)`` which yields the
   distance between locations. In addition, the same is provided for the
   *travel time*, which takes the velocity at which the vehicle moves into
   account.
3. The second function is `interp_dist(u,v, time_to_dest)`, and respectively
   `interp_time`. This interpolates a location on the space on the route
   between two points `u` and `v`, with the know remaining time `time_to_dest`.
   This is used to determine the current location of the vehicle when it is
   known that the vehicle is on the way to `v`, having started at `u`, and with
   remaining `time_to_dest = next_stop.estimated_arrival_time - current_time`.


