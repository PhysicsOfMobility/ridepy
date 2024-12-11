Module ``extras``
=================

This package contains additional functionality that is not a core part of the simulator but rather makes it more convenient to set up and use it. Currently this involves code for performing multiple simulations while varying parameters ("parameter scan"), reading and writing parameter sets and simulation output to and from disk as `JSON`_/`JSON Lines`_. In addition, convenience methods for easily creating graph transport spaces are included.


Simulations and Parameter Scans
-------------------------------

.. currentmodule:: ridepy.extras.simulation_set

This module allows to configure and execute a set of simulations while varying specific
parameters, i.e. performing a parameter scan.  The typical workflow is as follows:

.. code-block:: python

    # create SimulationSet instance
    simulation_set = SimulationSet(
        base_params={"general": {"n_reqs": 10}},
        product_params={"general": {"n_vehicles": [10, 100], "seat_capacity": [2, 8]}},
        data_dir=tmp_path,
        debug=True,
    )

    # execute simulations
    simulation_set.run()


Parameter Configuration
~~~~~~~~~~~~~~~~~~~~~~~

`SimulationSet` takes three main arguments: ``base_params``, ``zip_params`` and ``product_params``. Base parameters are parameters which are kept constant across all simulations defined by the simulation set. Here, the values of the inner dict are the actual parameters. For zip and product parameters, lists of values are supplied as the inner dictionary's values. Zip parameters are varied simultaneously across the simulations, i.e., the first simulation will use the first parameter value for all of the parameters in ``zip_params``, the second simulation will use the second parameter values, and so on. For zip parameters it is important that all lists of parameter values are of equal length. The lists in product parameters on the other hand will be multiplied as a Cartesian product. Here the lengths do not have to match, all possible combinations will be simulated.

Each of the arguments takes a dictionary of dictionaries. Currently, four top-level keys are supported: ``general``, ``dispatcher``, ``request_generator``, and ``analytics``. The inner dictionaries contain the actual parameters to be varied. The structure of the outer dictionary is thus as follows:

.. code-block:: python

      {
          "general": {...},
          "dispatcher": {...},
          "request_generator": {...},
          "analytics": {...},
      }

If any of the top-level keys are missing, the respective parameters are taken from the default base parameters.

Currently, the following parameters are supported:

* Valid keys for ``general``:

   * *Either* ``n_reqs: int`` *or* ``t_cutoff: float``. If setting ``t_cutoff``, ``n_reqs`` must be set to ``None`` and vice versa.
   * *Either* ``n_vehicles: int`` *and* ``initial_location: Location`` *or* ``initial_locations: dict[ID, Location]``. If setting ``initial_locations``, ``n_vehicles`` and ``initial_location`` must both be set to ``None`` and vice versa.
   * ``seat_capacity: int`` -- Seat capacity of the vehicles
   * ``space: TransportSpace`` -- The transport space to use
   * ``transportation_request_cls: Type[TransportationRequest]`` -- The `.TransportationRequest` class to use (primarily necessary to switch between the Python and Cython implementations)
   * ``vehicle_state_cls: Type[VehicleState]`` -- The `.VehicleState` class to use (again, primarily necessary to switch between the Python and Cython implementations)
   * ``fleet_state_cls: Type[FleetState]`` -- The `.FleetState` class to use (again, primarily necessary to switch between the Python and Cython implementations)

* Valid values for ``dispatcher``:

   * ``dispatcher_cls: Type[Dispatcher]`` -- The dispatcher type to use
   * Any dispatcher keyword argument, will be supplied to the dispatcher upon instantiation

* Valid values for ``request_generator``:

   * ``request_generator: Type[RequestGenerator]`` -- The request generator type to use
   * Any request generator keyword argument, will be supplied to the request generator upon instantiation

* Valid values for ``analytics``:

   * ``d_avg: float`` -- Average direct request distance.

As for the top-level keys, if any of the inner keys are missing, the respective parameters are taken from the default base parameters in `.SimulationSet`, which are currently set as follows:

.. code-block:: python

   {
       "general": {
           "n_reqs": 100,
           "t_cutoff": None,
           "space": Euclidean2D(coord_range=[(0, 1), (0, 1)], velocity=1),
           "n_vehicles": 10,
           "initial_location": (0, 0),
           "initial_locations": None,
           "seat_capacity": 8,
           "transportation_request_cls": ridepy.data_structures.TransportationRequest,
           "vehicle_state_cls": ridepy.vehicle_state.VehicleState,
           "fleet_state_cls": ridepy.fleet_state.SlowSimpleFleetState,
       },
       "dispatcher": {
           "dispatcher_cls": ridepy.util.dispatchers.ridepooling.BruteForceTotalTravelTimeMinimizingDispatcher
       },
       "request_generator": {
           "request_generator_cls": ridepy.util.request_generators.RandomRequestGenerator,
           "rate": 1,
       },
   }


In Cython mode, the respective Cython/C++ implementations of the `.TransportSpace`, `.Dispatcher`, `.TransportationRequest`, and `.VehicleState` classes are used:

.. code-block:: python

   {
       "general": {
           "n_reqs": 100,
           "t_cutoff": None,
           "space": Euclidean2D(velocity=1.0),
           "n_vehicles": 10,
           "initial_location": (0, 0),
           "initial_locations": None,
           "seat_capacity": 8,
           "transportation_request_cls": ridepy.data_structures_cython.data_structures.TransportationRequest,
           "vehicle_state_cls": ridepy.vehicle_state_cython.vehicle_state.VehicleState,
           "fleet_state_cls": ridepy.fleet_state.SlowSimpleFleetState,
       },
       "dispatcher": {
           "dispatcher_cls": ridepy.util.dispatchers_cython.dispatchers.BruteForceTotalTravelTimeMinimizingDispatcher
       },
       "request_generator": {
           "request_generator_cls": ridepy.util.request_generators.RandomRequestGenerator,
           "rate": 1,
       },
   }

The order of precedence is, last taking highest: ``default_base_params``, ``base_params``, ``zip_params``, ``product_params``.

Executing simulations
~~~~~~~~~~~~~~~~~~~~~

Simulations are executed when `SimulationSet.run()` is called. Independent simulations are performed through executing `.perform_single_simulation()` for each parameter set using multiprocessing. The events that are generated by the simulation are written to disk in the `JSON Lines`_ format. The simulation parameters are also written to disk, in separate `JSON`_ files.  This includes all data necessary to perform the respective simulation. For more detail, see :ref:`JSON IO`.  For each simulation run, a unique identfier is generated and the data is stored to ``<uuid>.jsonl`` for the events and ``<uuid>_params.json`` for the simulation parameters. The identifier hashes the parameter set, thereby allowing to continue an interrupted simulation set run later. The IDs generated can be retrieved using `SimulationSet.simulation_ids`. Alternatively the filenames of the resulting `JSON`_/`JSONL <JSON Lines_>`_ files are also directly available through `SimulationSet.param_paths` and `SimulationSet.event_paths`.


.. autoclass:: SimulationSet

    .. automethod:: run

    .. autoattribute:: simulation_ids

    .. autoattribute:: param_paths

    .. autoattribute:: event_paths

.. autofunction:: perform_single_simulation


Running analytics on the simulation results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simulation results can be automatically analyzed using the `ridepy.extras.analytics` module, storing the results to disk.

.. automethod:: SimulationSet.run_analytics

JSON IO
-------

.. currentmodule:: ridepy.extras.io

This IO module implements functionality for reading and writing to `JSON`_/`JSON Lines`_
format.

Simulation parameter configurations can be saved and restored using
`.save_params_json()` and `.read_params_json()`. The IO module handles serialization and
deserialization of the ``RequestGenerator``, the dispatcher and the ``TransportSpace``
used for the simulation. This allows to recreate any simulation from its saved parameter
dictionary. Note though that this *does not* serialize the actual objects. If the
implementation of e.g. the dispatcher is modified, the simulation result *will* change.

A list of simulation output events can be saved and restored using `.save_events_json()`
and `.read_events_json()`. The IO module handles serialization and deserialization of
the various event types:

* ``VehicleStateBeginEvent``
* ``VehicleStateEndEvent``
* ``PickupEvent``
* ``DeliveryEvent``
* ``RequestSubmissionEvent``
* ``RequestAcceptanceEvent``
* ``RequestRejectionEvent``

Later this can e.g. be used as input for the analytics module:

.. code-block:: python

    stops, requests = get_stops_and_requests(
        events=read_events_json("events.jsonl"), space=read_params_json("params.json")
    )

.. automodule:: ridepy.extras.io
    :members:

Spaces
------

.. currentmodule:: ridepy.extras.spaces

This module implements thin convenience wrappers around ``networkx`` to create common
network topologies to be used as transport spaces.

.. automodule:: ridepy.extras.spaces
    :members:


.. _JSON Lines: https://jsonlines.org/

.. _JSON: https://www.json.org/json-en.html
