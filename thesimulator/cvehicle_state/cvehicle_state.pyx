# distutils: language = c++
# distutils: sources = thesimulator/cvehicle_state/vstate.cpp

from data_structures cimport CyRequest
from vstate cimport handle_request


# TODO: Can we cdef enum class CRequest, and use CRequest from c++ code?

def create_and_handle_test_request():
    cdef CyRequest req
    req.request_id = "req1".encode('ascii')
    req.creation_timestamp = 123

    return handle_request(req)

