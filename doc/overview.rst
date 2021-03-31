Overview
========

.. highlight:: python

Here we describe the design of theSimulator, and how to get started with using
it to run simulations. We also describe how to specify new dispatching
algorithms and new transport spaces.



The setting
-----------
theSimulator does *not* do agent-based simulations. Rather, it starts with a set of
*transportation requests* (denoting the desire of an individual to be transported from A
to B within specified time windows), and a *dispatcher* (an algorithm that determines
which vehicle should service which requests and in which order). Then it simply
simulates these requests arriving in the system, being picked up and delivered. Requests
that cannot be delivered within the specified time windows are *rejected*.

theSimulator makes it easy to experiment with different dispatching algorithms,
spatiotemporal request densities, fleet sizes and transport spaces (2-D plane, different
graphs). It comes with an `analytics` module that computes from the simulation output
various metrics like the statistical distributions of occupancies, waiting times and
detours.

Since the ability to simulate many *requests* and many *vehicles* is important for any
quantitative study, we include two powerful ways of speeding up the simulation:

Using parallelism:
   The dispatcher interface prescribes computing a *cost* for serving a request with a
   certain vehicle. Then the vehicle with the minimum cost is chosen. Since this is an
   "embarassingly parallelizable" operation, theSimulator provides two parallel ways of
   computing it, out of the box:

   - ``multiprocessing``,
   - ``OpenMPI``.

Using `cython <https://cython.readthedocs.io/en/latest/>`_:
   We provide, out of the box, the ability to choose either pure pythonic or cythonic
   data structures and algorithms for running the simulations. This way, dispatchers can
   be defined in the C++ language. See :ref:`using_cython` for details.


Quickstart
----------
Here we will demonstrate how to run a simple simulation.

Generate requests
^^^^^^^^^^^^^^^^^
First we need to generate a sequence of :class:`TransportationRequest
<data_structures.TransportationRequest>`. Each ``TransportationRequest`` consists of:
  - ``origin``,
  - ``destination``,
  - ``pickup_timewindow_min``,
  - ``pickup_timewindow_max``,
  - ``delivery_timewindow_min``,
  - ``delivery_timewindow_max``. 

We will use the :mod:`request_generators <util.request_generators>` module to
generate some requests with random origins and destinations:

.. code-block:: python

    >>> import itertools as it
    >>> from thesimulator.util.spaces import Euclidean2D
    >>> from thesimulator.fleet_state import SlowSimpleFleetState
    >>> from thesimulator.data_structures import Stop, InternalRequest, StopAction
    >>> from thesimulator.util.request_generators import RandomRequestGenerator
    >>> from thesimulator.util.dispatchers import brute_force_distance_minimizing_dispatcher
    >>> from thesimulator.util.analytics import get_stops_and_requests
    >>> space = pyEuclidean2D()
    >>> request_rate = 1
    >>> rg = RandomRequestGenerator(
    ...            space=Euclidean2D(),
    ...            rate=request_rate,
    ...            )
    >>> num_requests = 2
    >>> reqs = list(it.islice(rg, num_requests))

Note that the ``origin`` and
``destination`` must belong to the same :class:`TransportSpace
<data_structures.TransportSpace>` (e.g. ``Euclidean2D``) where the simulation
will be run.


Create a ``FleetState`` with a single vehicle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We will now create a :class:`FleetState <fleet_state.FleetState>` with the
desired number of vehicles, the initian positions of the vehicles, and a
``dispatcher`` that matches a request to a vehicle.

.. code-block:: python

    >>> vehicle_id = 1
    >>> initial_location = (0, 0)
    >>> seat_capacity = 4
    >>> initial_stoplist = [Stop(
    ...            location=initial_location,
    ...            request=InternalRequest( #TODO Explain why the request_id should be -1
    ...                request_id=-1, creation_timestamp=0, location=initial_location
    ...            ),
    ...            action=StopAction.internal,
    ...            estimated_arrival_time=0,
    ...            occupancy_after_servicing=0,
    ...            time_window_min=0,
    ...            time_window_max=0,
    ...        )
    ...    ]
    >>> initial_stoplists = {vehicle_id: initial_stoplist}
    >>> fleet_state = SlowSimpleFleetState(
    ...    initial_stoplists=initial_stoplists,
    ...    space=Euclidean2D(),
    ...    seat_capacities=seat_capacity,
    ...    dispatcher=brute_force_distance_minimizing_dispatcher,
    ...    )


We have chosen one of the dispatchers provided in the :mod:`dispatchers
<thesimulator.util.dispatchers>` module. It is possible (and encouraged) to implement their
own.

Now, simulate
^^^^^^^^^^^^^
...by calling the :meth:`FleetState.simulate <fleet_state.FleetState.simulate>` method.
The output of the simulation run is an :any:`Iterator <python:collections.abc.Iterator>`
of ``Event`` objects, describing when which ``TransportationRequest`` was picked up and
delivered.

.. code-block:: python

    >>> events = list(fleet_state.simulate(reqs))
    >>> events
    [RequestAcceptanceEvent(request_id=0, timestamp=0.4692680899768591, origin=(0.6394267984578837, 0.025010755222666936), destination=(0.27502931836911926, 0.22321073814882275), pickup_timewindow_min=0.4692680899768591, pickup_timewindow_max=inf, delivery_timewindow_min=0.4692680899768591, delivery_timewindow_max=inf),
     PickupEvent(request_id=0, timestamp=1.1091838410432844, vehicle_id=1),
     DeliveryEvent(request_id=0, timestamp=1.5239955534224914, vehicle_id=1),
     RequestAcceptanceEvent(request_id=1, timestamp=3.4793895208943804, origin=(0.7364712141640124, 0.6766994874229113), destination=(0.8921795677048454, 0.08693883262941615), pickup_timewindow_min=3.4793895208943804, pickup_timewindow_max=inf, delivery_timewindow_min=3.4793895208943804, delivery_timewindow_max=inf),
     PickupEvent(request_id=1, timestamp=4.4795455315100465, vehicle_id=1),
     DeliveryEvent(request_id=1, timestamp=5.08951497443719, vehicle_id=1)]

..
    TODO Cross referencing modules with :mod:`bla` is not producing a hyperlink.


Using parallelism
-----------------
Running theSimulator in a multi-node OpenMPI cluster is as simple as replacing
:class:`SlowSimpleFleetState <fleet_state.SlowSimpleFleetState>` with
:class:`MPIFuturesFleetState <fleet_state.MPIFuturesFleetState>`:

.. code-block:: python
   :emphasize-lines: 4

    >>> space = Euclidean2D()
    >>> rg = RandomRequestGenerator(rate=10, space=space)
    >>> reqs = list(it.islice(rg, 1000))
    >>> fs = MPIFuturesFleetState(
         initial_stoplists=initial_stoplists,
         seat_capacities=[1] * len(initial_stoplists),
         space=space,
         dispatcher=taxicab_dispatcher_drive_first,
    )
    >>> events = list(fs.simulate(reqs, t_cutoff=20))


.. _using_cython:

Using cythonized data structures and algorithms
-----------------------------------------------
The simulation we saw can be sped up considerably by using a cythonized version of the
dispatcher, with the core logic implemented in C++. We will also need to use cythonized
versions of ``TransportationRequest``, ``Stop``, ``VehicleState`` and a
``TransportSpace``:


.. code-block:: python
   :emphasize-lines: 4,6,7,39
   :dedent: 1

    import itertools as it
    from thesimulator.util.spaces_cython import Euclidean2D
    from thesimulator.fleet_state import SlowSimpleFleetState
    from thesimulator.data_structures_cython import Stop, InternalRequest, TransportationRequest, StopAction
    from thesimulator.util.request_generators import RandomRequestGenerator
    from thesimulator.util.dispatchers_cython import brute_force_distance_minimizing_dispatcher
    from thesimulator.vehicle_state_cython import VehicleState as cy_VehicleState

    space = Euclidean2D()
    request_rate = 1
    rg = RandomRequestGenerator(
        space=Euclidean2D(),
        rate=request_rate,
        request_class=TransportationRequest
    )
    num_requests = 2
    reqs = list(it.islice(rg, num_requests))
    vehicle_id = 1
    initial_location = (0, 0)
    seat_capacity = 4
    initial_stoplist = [Stop(
        location=initial_location,
        request=InternalRequest(
            request_id=-1, creation_timestamp=0, location=initial_location
        ),
        action=StopAction.internal,
        estimated_arrival_time=0,
        occupancy_after_servicing=0,
        time_window_min=0,
        time_window_max=0,
    )
    ]
    initial_stoplists = {vehicle_id: initial_stoplist}
    fleet_state = SlowSimpleFleetState(
        initial_stoplists=initial_stoplists,
        space=Euclidean2D(),
        seat_capacities=seat_capacity,
        dispatcher=brute_force_distance_minimizing_dispatcher,
        vehicle_state_class=cy_VehicleState
    )
    events = list(fleet_state.simulate(reqs))
    print(events)


How to write your own dispatcher
---------------------------------



How to write your own ``TransportSpace``
-----------------------------------------


