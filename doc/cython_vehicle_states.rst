Cythonic VehicleState
---------------------
The class :class:`.vehicle_state_cython.VehicleState` is the cython implementation of the 
pure-python equivalent :class:`.vehicle_state.VehicleState`. They can be used interchangeably, 
but it is not possible to mix pure-python and cython components: If you want to go with the cythonic
:doc:`dispatchers<cython_dispatchers>`, then you need to use cythonic
:doc:`data_structures<cython_data_structures>` and :doc:`spaces<cython_spaces>`.

.. autoclass:: ridepy.vehicle_state_cython.VehicleState
    :members: fast_forward_time



