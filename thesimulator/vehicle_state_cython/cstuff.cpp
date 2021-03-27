
#include "cstuff.h"


using namespace std;
using namespace cstuff;

int main()
{
    int n = 1000;
    typedef pair<double, double> R2loc;
    //Euclidean2D space;
    Manhattan2D space;

    std::cout << "Hello from c++: " << space.d(std::make_pair(0,0), std::make_pair(5,9)) << std::endl;

    std::random_device rd;  //Will be used to obtain a seed for the random number engine
    std::mt19937 gen(rd()); //Standard mersenne_twister_engine seeded with rd()
    std::uniform_int_distribution<> distrib(0, 100);

    vector<Stop<R2loc>> stoplist;
    // populate the stoplist
    double arrtime = 0;
    double dist_from_last = 0;
    double dist = 0;
    Stop<R2loc> stop;
    shared_ptr<Request<R2loc>> req_ptr;
    pair<double, double> a, b;
    for (int i=0; i<n; i++)
    {
        pair<double, double> stop_loc = make_pair(distrib(gen), distrib(gen));
       if (i>0) dist = space.d(stop_loc, stop.location);

        arrtime = arrtime + dist;
        auto req_ptr = make_shared<TransportationRequest<R2loc>>(i, 0, make_pair(0,0), make_pair(0,1), 0, INFINITY, 0, INFINITY);

        stop = {stop_loc, req_ptr, StopAction::internal, arrtime, 0, INFINITY};


        stoplist.push_back(stop);
    }
    //debug
    std::cout<<"begin debug:"<<std::endl;
    std::cout<<stoplist[0].estimated_arrival_time<<std::endl;
    stoplist[0].estimated_arrival_time = 8.4362;
    std::cout<<stoplist[0].estimated_arrival_time<<std::endl;

    // create new request
    R2loc req_origin = make_pair(distrib(gen), distrib(gen));
    R2loc req_dest = make_pair(distrib(gen), distrib(gen));

    auto request_ptr = make_shared<TransportationRequest<R2loc>>(42, 1, req_origin, req_dest, 0, INFINITY, 0, INFINITY);

    auto start = std::chrono::system_clock::now();
    auto x = brute_force_time_minimizing_dispatcher(request_ptr, stoplist, space);
    auto end = std::chrono::system_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "Time taken: " << elapsed.count() << " s" << std::endl;
    std::cout << x.min_cost << endl;
}