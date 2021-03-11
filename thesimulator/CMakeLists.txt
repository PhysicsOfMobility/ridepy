cmake_minimum_required(VERSION 3.10)

# set the project name
project(thesimulator)

# add the MathFunctions library
add_subdirectory(vehicle_state_cython)
add_subdirectory(data_structures_cython)
add_subdirectory(util)

# add the executable
add_executable(
        dispatcher vehicle_state_cython/cstuff.cpp util/spaces_cython/cspaces.cpp)

# specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)