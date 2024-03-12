from ridepy.util.dispatchers.taxicab import TaxicabDispatcherDriveFirst
from ridepy.util.dispatchers.ridepooling import (
    BruteForceTotalTravelTimeMinimizingDispatcher,
)

"""
This package contains pure python dispatchers. These are callable from python and should be used for testing 
purposes and small scale simulations where computing performance is not of primary concern. For larger scale 
simulations, use Cython dispatchers. Note that those can not be called from python directly, but through the 
`.vehicle_state_cython.VehicleState` class.
"""
