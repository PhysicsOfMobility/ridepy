add_library(dispatchers INTERFACE)
find_package(ortools CONFIG REQUIRED)
target_include_directories(dispatchers INTERFACE ./)
target_link_libraries(dispatchers INTERFACE ortools::ortools)
