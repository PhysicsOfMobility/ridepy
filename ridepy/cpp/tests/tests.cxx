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


    cout << excCharInit;
    // init transport space: an (infinit) square grid
    const double gridSize = 1.;
    const double velocity = 2.;
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
    int i=0;
    for (R2loc location : fleet.currentVehiclePositions())
        cout << "[INIT]     " << std::setw(3) << i++ << ":  " << location << endl;

    cout << excCharInfo
         << "[INFO] expected loactions:" << endl;
    i = 0;
    for (R2loc location : initialLocations)
        cout << "[INFO]     " << std::setw(3) << i++ << ":  " << gridSize * location << endl;
    cout << excCharInit;

    // generate transportation requests
    const double timestep_per_request = 0.5;
    std::vector<TransportationRequest<I2loc>> requests;
    requests.push_back(TransportationRequest<I2loc>(requests.size(),requests.size()*timestep_per_request,{1,2},{0,0}));
    //requests.push_back(TransportationRequest<I2loc>(requests.size(),requests.size()*timestep_per_request,{-3,0},{1,1}));

    cout << "[INIT] create transportation requests:" << endl;
    for (auto request : requests)
        cout << "[INIT]   " << std::setw(3) << request.request_id << ":  t=" << std::setprecision(3) << std::fixed << request.creation_timestamp
                            << "   " << request.origin << " -> " << request.destination << endl;

    // run simulation
    cout << excCharRun
         << "[RUN] start simulation..." << endl;
    const double timeStep = 0.1;
    const int maxTimeSteps = 31;
    auto it = requests.begin();
    for (int i=0; i<maxTimeSteps; i++){
        const double curTime = i*timeStep;
        cout << "[RUN] ---------------------------" << endl
             << "[RUN] --- time: " << curTime << endl
             << "[RUN] ---------------------------" << endl
             << "[RUN] fast forward ..." << endl;
        // fast forward time
        std::vector<StopEvent> stopEvents = fleet.fast_forward(curTime);
        if (stopEvents.size()>0){
            cout << "[RUN] the following events occured during fast forward:" << endl;
            for (const StopEvent &e : stopEvents)
                cout << "[RUN]   t=" << e.timestamp << ": req=" << e.requestId
                     << ", vehicle=" << e.vehicleId
                     << ", action='" << (e.action == StopAction::DROPOFF ? "dropoff" : e.action == StopAction::PICKUP ? "pickup" : "internal") << "'"
                     << endl;
        }

        cout << excCharInfo
             << "[INFO] current vehicle positions:" << endl;
        int v=0;
        for (R2loc location : fleet.currentVehiclePositions())
            cout << "[INFO]   " << std::setw(3) << v++ << ":  " << location << endl;
        cout << excCharRun
             << "[RUN] process requests ..." << endl;

        // process all due transportation requests
        while (it != requests.end() && it->creation_timestamp <= curTime){
            cout << "[RUN] submit request " << it->request_id << endl
                 << "        t=" << it->creation_timestamp << endl
                 << "        from " << it->origin << endl
                 << "        to   " << it->destination << endl
                 << "        pickup window: "   << it->pickup_timewindow << endl
                 << "        delivery window: " << it->delivery_timewindow << endl;
            RequestEvent e1 = fleet.submit_transportation_request(*it);
            cout << "[RUN] feedback from dispatcher:" << endl
                 << "        request_id: " << e1.requestId << endl
                 << "        comment:    " << e1.comment   << endl
                 << "        timestamp:  " << e1.timestamp << endl
                 << "        estimated in-vehicle time: " << e1.estimated_invehicle_time << endl;
            if (e1.type == EventType::REQUESTOFFERING_EVENT){
                // accept ride
                cout << "[RUN] accept the ride" << endl;
                RequestEvent e2 = fleet.execute_transportation_request(it->request_id);
                if (e2.type == EventType::REQUESTACCEPTION_EVENT)
                    cout << "[RUN] ride was accepted. Message from fleet: " << e2.comment << endl;
                else
                    cout << excCharError
                         << "[ERROR] ride was rejected from fleet. This should not happen at this point. Message from fleet: " << e2.comment << endl
                         << excCharRun;
            } else {
                // this request can't be serviced :(
                cout << "[RUN] this request can't be serviced." << endl;
            }
            // forward to next request
            it++;
        }
    }


    cout << excCharDefault;
}
