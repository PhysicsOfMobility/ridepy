# distutils: language = c++
from .cspaces cimport(
    R2loc,
    Euclidean2D as CEuclidean2D,
    Manhattan2D as CManhattan2D,
)

from thesimulator.cdata_structures.data_structures cimport LocType, R2loc

from cython.operator cimport dereference

"""
Note: We are duplicating the c++ class hierarchy in ./cspaces.h. In short, our c++ transport spaces
all inherit from the abstract base class TransportSpace. Here, we will create a cdef class also called
TransportSpace and other cdef classes will inherit from that. There are a few caveats, which were described
in great length at https://stackoverflow.com/a/28727488. Basically:

1. Virtual functions that are later overridden in a child class **must be declared only for the base class**.
   That is, we must *not* declare Euclidean2D.d/t/... here, only in TransportSpace.
   Doing so will result in an *ambiguous overridden function* error from cython.
2. When allocating/deallocating c pointers in __cinit__/__dealloc__ of a cdef class ClassLaterSubclassedFrom 
   that has been subclassed, a check like `if type(self) == ClassLaterSubclassedFrom` must be used. Otherwise
   double free occurs. 
"""

#cdef class TransportSpace:
#    """
#    We do not need to allocate/free self.c_space_ptr at all since This is a wrapper around the c++ abstract class
#    and will never be instantiated.
#    """
#    # TODO: Need to template away to eliminate hard requirement that locations are R2loc.
#    # However, does anything need to be done at all apart from removing all the type declarations from the
#    # method arguments?
#    def d(self, R2loc u, R2loc v):
#        return dereference(self.c_space_ptr).d(u, v)
#
#    def t(self, R2loc u, R2loc v):
#        return dereference(self.c_space_ptr).t(u, v)
#
#    def interp_dist(self, R2loc u, R2loc v, double dist_to_dest):
#        return dereference(self.c_space_ptr).interp_dist(u, v, dist_to_dest)
#
#    def interp_time(self, R2loc u, R2loc v, double time_to_dest):
#        return dereference(self.c_space_ptr).interp_time(u, v, time_to_dest)


#cdef class TransportSpaceR2loc:
#    """
#    We do not need to allocate/free self.c_space_ptr at all since This is a wrapper around the c++ abstract class
#    and will never be instantiated.
#    """
#    # TODO: Need to template away to eliminate hard requirement that locations are R2loc.
#    # However, does anything need to be done at all apart from removing all the type declarations from the
#    # method arguments?
#    def d(self, R2loc u, R2loc v):
#        return dereference(self.c_space_ptr).d(u, v)
#
#    def t(self, R2loc u, R2loc v):
#        return dereference(self.c_space_ptr).t(u, v)
#
#    def interp_dist(self, R2loc u, R2loc v, double dist_to_dest):
#        return dereference(self.c_space_ptr).interp_dist(u, v, dist_to_dest)
#
#    def interp_time(self, R2loc u, R2loc v, double time_to_dest):
#        return dereference(self.c_space_ptr).interp_time(u, v, time_to_dest)
#



cdef class TransportSpace:
    def __init__(self, loc_type):
        if loc_type == 'int':
            self.loc_type = LocType.INT
        elif loc_type == 'r2loc':
            self.loc_type = LocType.R2LOC
        else:
            raise ValueError("This line should never have been reached")

    def d(self, u, v):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).d(<R2loc>u, <R2loc>v)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).d(<int>u, <int>v)
        else:
            raise ValueError("This line should never have been reached")

    def t(self, u, v):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).t(<R2loc>u, <R2loc>v)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).t(<int>u, <int>v)

    def interp_dist(self, u, v, double dist_to_dest):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).interp_dist(<R2loc>u, <R2loc>v, dist_to_dest)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).interp_dist(<int>u, <int>v, dist_to_dest)
        else:
            raise ValueError("This line should never have been reached")

    def interp_time(self, u, v, double time_to_dest):
        if self.loc_type == LocType.R2LOC:
            return dereference(self.u_space.space_r2loc_ptr).interp_time(<R2loc>u, <R2loc>v, time_to_dest)
        elif self.loc_type == LocType.INT:
            return dereference(self.u_space.space_int_ptr).interp_time(<int>u, <int>v, time_to_dest)
        else:
            raise ValueError("This line should never have been reached")

    def __dealloc__(self):
        #free the correct pointer
        ...


cdef class Euclidean2D(TransportSpace):
    def __cinit__(self, double velocity=1):
        self.loc_type == LocType.R2LOC
        self.derived_ptr = self.u_space.space_r2loc_ptr = new CEuclidean2D(velocity)

    def __dealloc__(self):
        del self.derived_ptr


cdef class Manhattan2D(TransportSpace):
    def __cinit__(self, double velocity=1):
        self.loc_type == LocType.R2LOC
        self.derived_ptr = self.u_space.space_r2loc_ptr = new CManhattan2D(velocity)

    def __dealloc__(self):
        del self.derived_ptr

