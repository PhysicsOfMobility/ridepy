#include "tests.h"

#include <iostream>
using std::cout;
using std::endl;

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



    // test fleetstate

    FleetState<I2loc> fleet(10,8,I2loc(0,0),&testSpace,new BruteForceTotalTravelTimeMinimizingDispatcher<I2loc>());


}

void test_simpleSquareGridSimulation(){

}
