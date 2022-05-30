#include <iostream>
using std::cout;
using std::endl;

#include <random>
#include <chrono>

#include <vector>

#include "ridepy/r2loc.h"
#include "ridepy/transportationrequest.h"

using namespace ridepy;

int main() {

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

    return 0;
}
