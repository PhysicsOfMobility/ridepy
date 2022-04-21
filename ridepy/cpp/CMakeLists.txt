# In this subdirectory, a pure C++ version of RidePy can be build by running the CMake script in this file.
# it outputs a linkable C++ library  *libRidePy.a* and an executable *ridepy-cpp-test* to run some tests
cmake_minimum_required(VERSION 3.5)

project(ridepy-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(RidePy
    ../util/spaces_cython/cspaces.cxx
)

add_executable(ridepy-cpp-test main.cpp)
