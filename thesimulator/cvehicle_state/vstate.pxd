from libcpp.string cimport string

cdef extern from "vstate.cpp" namespace "cstates":
    cdef cppclass CRequest:
        CRequest(string request_id, float creation_timestamp)
        CRequest()
        string request_id
        float creation_timestamp

