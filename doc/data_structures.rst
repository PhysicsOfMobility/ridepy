Data Structures
---------------
.. currentmodule:: ridepy


The module contains the data structures `.FleetState` and `.VehicleState` depend on.

..
    TODO The automodule leads to a very dense output. We should add more normal docs in between the autodocs.

Requests
~~~~~~~~

.. automodule:: ridepy.data_structures
    :members: Request, TransportationRequest, InternalRequest


LocType
~~~~~~~
.. automodule:: ridepy.data_structures
    :members: LocType

Stop and Stoplist
~~~~~~~~~~~~~~~~~

.. automodule:: ridepy.data_structures
    :members: Stop, StopAction

The `TransportSpace` and `Dispatcher` interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ridepy.data_structures.TransportSpace
    :members:

.. note::
   This is only the abstract base class specifying the *interface*. Actual
   `TransportSpace` classes are available in `.util.spaces`.

.. automodule:: ridepy.data_structures
    :members: SingleVehicleSolution, Dispatcher


