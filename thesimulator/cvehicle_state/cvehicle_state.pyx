# distutils: language = c++
# distutils: sources = thesimulator/cvehicle_state/vstate.cpp

from vstate cimport CRequest
from data_structures cimport  FooBar


# TODO: Can we cdef enum class CRequest, and use CRequest from c++ code?



cdef class Request:
    cdef CRequest crequest
    cdef FooBar test
    def __cinit__(self, request_id, creation_timestamp):
        self.crequest = CRequest(request_id.encode('ascii'), float(creation_timestamp))
        print(self.test.name)
