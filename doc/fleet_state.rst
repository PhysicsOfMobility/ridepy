FleetState
==========
.. currentmodule:: ridepy.fleet_state

The ``FleetState`` class is the core component that a user needs in order to setting up
and running a simulation using ridepy, as described in :doc:`overview`. Once the
user creates a ``FleetState`` with the desired number of vehicles of appropriate
capacities and initial positions, a simulation can be run by calling
`FleetState.simulate()`, supplying iterator or requests. The ``FleetState`` advances the
simulator "clock", processes the `.TransportationRequest` objects one by one, "moves"
the vehicles so that they pick up and deliver the requests. It yields a sequence of
`.Event` objects describing what happened during the simulation.

The `FleetState` interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

The `fleet_state` module contains an abstract base class `.FleetState` that defines the
following interface, which is implemented in different inherited classes using different
strategies for performing the core computations.

.. autoclass:: FleetState
    :members:
    :private-members:

Different implementations of the `FleetState` interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Two different implementations of this base class are included:

`SlowSimpleFleetState`
    Performs all computations in a single process without any
    paralllelization.
`MPIFuturesFleetState`
    Uses `mpi4py.futures
    <https://mpi4py.readthedocs.io/en/stable/mpi4py.futures.html>`_ to
    parallelize the computations.

These two implementations will produce identical output (i.e. sequence of `Event`
objects) if the input parameters are identical. The users are of course free to
implement their own subclass of `FleetState` in order to parallelize the core
computations differently, e.g. by using job schedulers or multiprocessing. 

.. autoclass:: SlowSimpleFleetState
    :members:

.. autoclass:: MPIFuturesFleetState
    :members:
