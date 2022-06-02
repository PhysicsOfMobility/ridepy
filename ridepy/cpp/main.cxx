#include <iostream>
using std::cout;
using std::endl;

#include <string>

#include "tests/tests.h"

int main(const int argc, char *argv[]) {

    cout << "start RidePy C++ tests..." << endl;
    // The test case that should be executed can be choosen using a command line argument.
    // If no or an unknown mode name is specified, the test_misc() function will be called.
    const std::string mode = argc>1 ? argv[1] : "";

    cout << "using mode '" << mode << "'." << endl
         << "---------------------------------" << endl;

    if (mode == "simpleSquareGrid"){
        test_simpleSquareGridSimulation();
    // to include new test cases, just add another else if here
    } else {
        test_misc();
    }

    return 0;
}
