# In this subdirectory, a pure C++ version of RidePy can be build by running the CMake script in this file.
# it outputs a linkable C++ library  *libRidePy.a* and an executable *ridepy-cpp-test* to run some tests
cmake_minimum_required(VERSION 3.5)

project(ridepy-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# build library
file(GLOB RIDEPY_FILES
    ridepy/*.h
    ridepy.dox
)
add_library(RidePy
    ${RIDEPY_FILES}
    # TransportSpace
    ../util/spaces_cython/transportspace.h
    ../util/spaces_cython/cspaces.h
    ../util/spaces_cython/cspaces.cxx
    # VehicleState
    ../vehicle_state_cython/cvehicle_state.h
    # FleetState
    ../fleet_state/fleetstate.h
    # DataStructures
    ../data_structures_cython/cdata_structures.h
    # Dispatchers
    ../util/dispatchers_cython/cdispatchers.h
    ../util/dispatchers_cython/cdispatchers_utils.h
)

# ensure, that header files can be included when linking this library from other projects
target_include_directories(RidePy PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# build test executable
add_executable(RidePy-cpp-test main.cxx)
target_link_libraries(RidePy-cpp-test RidePy)
