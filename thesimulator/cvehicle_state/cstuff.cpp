
#include "cstuff.h"


using namespace std;
using namespace cstuff;
int main()
{
    int n = 1000;
    Euclidean2D space;

    std::random_device rd;  //Will be used to obtain a seed for the random number engine
    std::mt19937 gen(rd()); //Standard mersenne_twister_engine seeded with rd()
    std::uniform_int_distribution<> distrib(0, 100);

    vector<Stop> stoplist;
    // populate the stoplist
    double arrtime = 0;
    double dist_from_last = 0;
    double dist = 0;
    Stop stop;
    pair<double, double> a, b;
    for (int i=0; i<n; i++)
    {
        pair<double, double> stop_loc = make_pair(distrib(gen), distrib(gen));
        if (i>0) dist = space.d(stop_loc, stop.location);

        arrtime = arrtime + dist;
        Request dummy_req {i, 0, make_pair(0,0), make_pair(0,1), 0, INFINITY, 0, INFINITY};
        stop = {stop_loc, dummy_req, StopAction::internal, arrtime, 0, INFINITY};

        stoplist.push_back(stop);
    }
    // create new request
    pair<double, double> req_origin = make_pair(distrib(gen), distrib(gen));
    pair<double, double> req_dest = make_pair(distrib(gen), distrib(gen));
    Request request {42, 1, req_origin, req_dest, 0, INFINITY, 0, INFINITY};

    auto start = std::chrono::system_clock::now();
    auto x = brute_force_distance_minimizing_dispatcher(request, stoplist, space);
    auto end = std::chrono::system_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "Time taken: " << elapsed.count() << " s" << std::endl;
    std::cout << x.min_cost << endl;
}