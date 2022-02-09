# distutils: language=c++

from ridepy.data_structures_cython.data_structures cimport  LocType, R2loc

from .cdispatchers cimport (
AbstractDispatcher as CAbstractDispatcher,
BruteForceTotalTravelTimeMinimizingDispatcher as CBruteForceTotalTravelTimeMinimizingDispatcher,
BruteForceTotalTravelTimeMinimizingStopMergingDispatcher as CBruteForceTotalTravelTimeMinimizingStopMergingDispatcher,
SimpleEllipseDispatcher as CSimpleEllipseDispatcher,
ExternalCost
)


cdef class Dispatcher:
    def __init__(self, loc_type, *args, **kwargs):
        self.loc_type = loc_type

    def __dealloc__(self):
        if self.loc_type == LocType.R2LOC:
            del self.u_dispatcher.dispatcher_r2loc_ptr
        elif self.loc_type == LocType.INT:
            del self.u_dispatcher.dispatcher_int_ptr
        else:
            raise ValueError("This line should never have been reached")

    def __reduce__(self):
        return self.__class__, (self.loc_type, )


cdef class BruteForceTotalTravelTimeMinimizingDispatcher(Dispatcher):
    def __cinit__(self, loc_type, external_cost=ExternalCost.absolute_detour):
        if loc_type == LocType.R2LOC:
            self.u_dispatcher.dispatcher_r2loc_ptr = (
                new CBruteForceTotalTravelTimeMinimizingDispatcher[R2loc](external_cost)
                )
        elif loc_type == LocType.INT:
            self.u_dispatcher.dispatcher_int_ptr = (
                new CBruteForceTotalTravelTimeMinimizingDispatcher[int](external_cost)
            )
        else:
            raise ValueError("This line should never have been reached")

cdef class BruteForceTotalTravelTimeMinimizingStopMergingDispatcher(Dispatcher):
    def __cinit__(self, loc_type, external_cost=ExternalCost.absolute_detour, merge_radius=1.):
        if loc_type == LocType.R2LOC:
            self.u_dispatcher.dispatcher_r2loc_ptr = (
                new CBruteForceTotalTravelTimeMinimizingStopMergingDispatcher[R2loc](external_cost, merge_radius)
                )
        elif loc_type == LocType.INT:
            self.u_dispatcher.dispatcher_int_ptr = (
                new CBruteForceTotalTravelTimeMinimizingStopMergingDispatcher[int](external_cost, merge_radius)
            )
        else:
            raise ValueError("This line should never have been reached")

cdef class SimpleEllipseDispatcher(Dispatcher):
    def __cinit__(self, loc_type, max_relative_detour=0):
        if loc_type == LocType.R2LOC:
            self.u_dispatcher.dispatcher_r2loc_ptr = new CSimpleEllipseDispatcher[R2loc](max_relative_detour)
        elif loc_type == LocType.INT:
            self.u_dispatcher.dispatcher_int_ptr = new CSimpleEllipseDispatcher[int](max_relative_detour)
        else:
            raise ValueError("This line should never have been reached")