#include "tests.h"

#include <iostream>
using std::cout;
using std::endl;
#include <iomanip>

#include <random>
#include <chrono>

#include <vector>

#include "ridepy/r2loc.h"
#include "ridepy/transportationrequest.h"

#include "ridepy/euclidean2d.h"
#include "ridepy/squaregrid.h"
#include "ridepy/fleetstate.h"
#include "ridepy/bruteforcetotaltraveltimeminimisingdispatcher.h"

using namespace ridepy;

void test_misc(){
    cout << "start default test routine" << endl;

    std::minstd_rand0 generator(std::minstd_rand0(std::chrono::system_clock::now().time_since_epoch().count()));
    std::uniform_real_distribution<double> distribution(std::uniform_real_distribution<double>(0.0,1.0));

    // generate 20 random TransportationRequests
    std::vector<TransportationRequest<R2loc>> requests;
    for (int i=0; i<20; i++){
        const double requestTime = 0.1 * i;
        R2loc origin = {distribution(generator),distribution(generator)};
        R2loc destination = {distribution(generator),distribution(generator)};
        requests.emplace_back(TransportationRequest<R2loc>(i,requestTime,origin,destination));
    }

    cout << "transportation requests:" << endl;
    for (auto request : requests)
        cout << std::fixed << request.request_id << ":\t" << request.origin << " -> " << request.destination << endl;

    // test TransportSpace
    SquareGrid testSpace(4,2);

    R2loc origin = {0,0};
    R2loc destinantion = {1,1};

    cout << "distance:    " << testSpace.d(origin,destinantion) << endl;
    cout << "travel time: " << testSpace.t(origin,destinantion) << endl;
    cout << "interp_dist: " << testSpace.interp_dist(origin,destinantion,4.1) << endl;
    cout << "interp_time: " << testSpace.interp_time(origin,destinantion,2) << endl;
}

void test_simpleSquareGridSimulation(){
    cout << "start test case 'simple square grid simulation'" << endl;

    // init transport space: an (infinit) square grid
    const double gridSize = 2.;
    const double velocity = 4.;
    SquareGrid *space = new SquareGrid(gridSize,velocity);
    cout << "[INIT] create transport space: a square grid with grid size " << space->gridSize() << " and velocity " << space->velocity() << endl;

    // create dispatcher
    AbstractDispatcher<I2loc> *dispatcher = new BruteForceTotalTravelTimeMinimizingDispatcher<I2loc>;
    cout << "[INIT] create dispatcher: use BruteForceTotalTravelTimeMinimizingDispatcher" << endl;

    // init fleet
    const int seat_capacity = 8;
    std::vector<I2loc> initialLocations;
    initialLocations.push_back({2,0});
    initialLocations.push_back({-2,0});
    const int numVehicles = initialLocations.size();

    FleetState<I2loc> fleet(numVehicles,seat_capacity,initialLocations,space,dispatcher);
    cout << "[INIT] create fleet with " << fleet.numVehicles() << " vehicles, each having a seat capacity of " << seat_capacity << "." << endl
         << "[INIT]   the vehicles are initialy located here:" << endl;
    std::vector<R2loc> locations = fleet.currentVehiclePositions();
    int i=0;
    for (R2loc location : locations)
        cout << "[INIT]     " << std::setw(3) << i++ << ":  " << location << endl;

    cout << "[INFO] expected loactions:" << endl;
    i = 0;
    for (R2loc location : initialLocations)
        cout << "[INFO]     " << std::setw(3) << i++ << ":  " << gridSize * location << endl;
}
