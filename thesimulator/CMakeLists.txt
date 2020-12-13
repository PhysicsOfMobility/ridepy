cmake_minimum_required(VERSION 3.10)

# set the project name
project(thesimulator)

# add the MathFunctions library
add_subdirectory(cvehicle_state)
add_subdirectory(cdata_structures)
add_subdirectory(util)

# add the executable
add_executable(
        dispatcher cvehicle_state/cstuff.cpp util/cspaces/cspaces.cpp util/bla.cpp cdata_structures/cdata_structures.cpp
        util/cdispatchers/cdispatchers.cpp util/cdispatchers/cdispatchers_utils.cpp)

# specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)