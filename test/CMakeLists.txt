include(FetchContent)
FetchContent_Declare(
        googletest
        # Specify the commit you depend on and update it regularly.
        URL https://github.com/google/googletest/archive/609281088cfefc76f9d0ce82e1ff6c30cc3591e5.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# adding the Google_Tests_run target
add_executable(tests_run cpp_integration_test.cpp)

# linking Google_Tests_run with DateConverter_lib which will be tested
add_executable(
        integration_test_insertion cpp_integration_test.cpp ../ridepy/util/spaces_cython/cspaces.cxx)
target_link_libraries(integration_test_insertion LINK_PUBLIC dispatchers gtest gtest_main)
# target_link_libraries(integration_test_insertion gtest gtest_main)
