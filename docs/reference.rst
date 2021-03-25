Reference
=========

How does theSimulator run simulations?
--------------------------------------
The user needs to create a `FleetState` object, specifying the number of
vehicles desired and their initial positions. Then one can call
`FleetState.simulate()` with an :any:`Iterator
<python:collections.abc.Iterator>` of `TransportationRequest`, which leads
to:

1. The `FleetState` fetching the next request from the iterator.


which is just a thin wrapper around a dictionary mapping
``vehicle_id``'s to `VehicleState`'s.


.. toctree::
   :maxdepth: 5
   :caption: Contents:

   fleet_state
   vehicle_state
   data_structures
   utils
   cythonic_stuff
