cmake_minimum_required(VERSION 3.19)

# set the project name
project(ridepy)

add_subdirectory(vehicle_state_cython)
add_subdirectory(data_structures_cython)
add_subdirectory(util)

# specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
