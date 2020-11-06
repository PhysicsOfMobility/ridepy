# distutils: language = c++

from libcpp.string cimport string

cdef public struct CyRequest:
    string request_id
    float creation_timestamp