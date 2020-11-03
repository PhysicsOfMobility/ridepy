# distutils: language = c++
# distutils: sources = vstate.cpp

from vstate cimport CRequest
from libcpp.string cimport string


cdef class Request:
    cdef CRequest crequest

    def __cinit__(self, string request_id, float creation_timestamp):
        self.crequest = CRequest(request_id, creation_timestamp)

