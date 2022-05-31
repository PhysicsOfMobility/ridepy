# In this subdirectory, a pure C++ version of RidePy can be build by running the CMake script in this file.
# it outputs a linkable C++ library  *libRidePy.a* and an executable *ridepy-cpp-test* to run some tests
cmake_minimum_required(VERSION 3.5)

project(ridepy-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# build library
file(GLOB_RECURSE RIDEPY_FILES
    ridepy/*.cxx
    ridepy/*.h
)
add_library(RidePy ${RIDEPY_FILES})

# set linker language manually as for some reasons CMake has problems otherwise
set_target_properties(RidePy PROPERTIES LINKER_LANGUAGE CXX)

# ensure, that header files can be included when linking this library from other projects
target_include_directories(RidePy PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# build test executable
add_executable(RidePy-cpp-test main.cxx)
target_link_libraries(RidePy-cpp-test RidePy)


# build target for Doxygen files
file(GLOB_RECURSE DOX_FILES
    Doxyfile
    *.dox
)
add_custom_target(RidePy-doxygen ALL SOURCES ${DOX_FILES})
