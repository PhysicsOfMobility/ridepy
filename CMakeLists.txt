cmake_minimum_required(VERSION 3.19)
# set the project name
project(ridepy)

add_subdirectory(ridepy)
add_subdirectory(test)

# Uncomment the following line to see detailed logs for the compilation process
# set(CMAKE_VERBOSE_MAKEFILE on)
# add the executable

# specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)