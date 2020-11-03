# distutils: language = c++
# distutils: sources = thesimulator/cvehicle_state/vstate.cpp

from vstate cimport CRequest
from libcpp.string cimport string


cdef class Request:
    cdef CRequest crequest

    def __cinit__(self, request_id, creation_timestamp):
        self.crequest = CRequest(request_id.encode('ascii'), float(creation_timestamp))

