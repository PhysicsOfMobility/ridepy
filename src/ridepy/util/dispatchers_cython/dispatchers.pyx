# distutils: language=c++

from ridepy.data_structures_cython.data_structures cimport  LocType, R2loc

from .cdispatchers cimport (
AbstractDispatcher as CAbstractDispatcher,
BruteForceTotalTravelTimeMinimizingDispatcher as CBruteForceTotalTravelTimeMinimizingDispatcher,
SimpleEllipseDispatcher as CSimpleEllipseDispatcher,
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
    def __cinit__(self, loc_type):
        if loc_type == LocType.R2LOC:
            self.u_dispatcher.dispatcher_r2loc_ptr = (
                new CBruteForceTotalTravelTimeMinimizingDispatcher[R2loc]()
                )
        elif loc_type == LocType.INT:
            self.u_dispatcher.dispatcher_int_ptr = (
                new CBruteForceTotalTravelTimeMinimizingDispatcher[int]()
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