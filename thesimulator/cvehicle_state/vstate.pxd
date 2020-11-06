# distutils: language = c++

from libcpp.string cimport string
from data_structures cimport CyRequest

cdef extern from "vstate.h":
    int handle_request(CyRequest req)

