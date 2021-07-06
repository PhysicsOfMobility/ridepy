
#include "cpp_integration_test.h"
#include "gtest/gtest.h"

using namespace std;
using namespace cstuff;

double inf = 100000000;

TEST(RidepyTest, integration) {
  int n = 1000;
  typedef pair<double, double> R2loc;
  // Euclidean2D space;
  Manhattan2D space;

  std::cout << "Hello from c++: "
            << space.d(std::make_pair(0, 0), std::make_pair(5, 9)) << std::endl;

  std::random_device
      rd; // Will be used to obtain a seed for the random number engine
  std::mt19937 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
  std::uniform_int_distribution<> distrib(0, 100);

  vector<Stop<R2loc>> stoplist;
  // populate the stoplist
  double arrtime = 0;
  double dist_from_last = 0;
  double dist = 0;
  Stop<R2loc> stop;
  shared_ptr<Request<R2loc>> req_ptr;
  pair<double, double> a, b;
  for (int i = 0; i < n; i++) {
    pair<double, double> stop_loc = make_pair(distrib(gen), distrib(gen));
    if (i > 0)
      dist = space.d(stop_loc, stop.location);

    arrtime = arrtime + dist;
    auto req_ptr = make_shared<TransportationRequest<R2loc>>(
        i, 0, make_pair(0, 0), make_pair(0, 1), 0, inf, 0, inf);

    stop = {stop_loc, req_ptr, StopAction::internal, arrtime, 0, 0, inf};

    stoplist.push_back(stop);
  }
  // debug
  std::cout << "begin debug:" << std::endl;
  std::cout << stoplist[0].estimated_arrival_time << std::endl;
  stoplist[0].estimated_arrival_time = 8.4362;
  std::cout << stoplist[0].estimated_arrival_time << std::endl;

  // create new request
  R2loc req_origin = make_pair(distrib(gen), distrib(gen));
  R2loc req_dest = make_pair(distrib(gen), distrib(gen));

  auto request_ptr = make_shared<TransportationRequest<R2loc>>(
      42, 1, req_origin, req_dest, 0, inf, 0, inf);

  auto start = std::chrono::system_clock::now();
  auto x = brute_force_total_traveltime_minimizing_dispatcher(
      request_ptr, stoplist, space, 10);
  auto end = std::chrono::system_clock::now();

  std::chrono::duration<double> elapsed = end - start;
  std::cout << "Time taken: " << elapsed.count() << " s" << std::endl;
  std::cout << x.min_cost << endl;

  vector<vector<Stop<R2loc>>> stoplists(1, stoplist);
  vector<int> capacities{10};
  std::cout << "Ran ortools" << std::endl;
}

TEST(RidepyTest, integration_fleetstate) {
  int n = 1000;
  typedef pair<double, double> R2loc;
  // Euclidean2D space;
  Manhattan2D space;

  std::random_device
      rd; // Will be used to obtain a seed for the random number engine
  std::mt19937 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
  std::uniform_int_distribution<> distrib(0, 100);

  vector<Stop<R2loc>> stoplist;
  // populate the stoplist
  double arrtime = 0;
  double dist_from_last = 0;
  double dist = 0;
  Stop<R2loc> stop;
  shared_ptr<Request<R2loc>> req_ptr;
  pair<double, double> a, b;
  for (int i = 0; i < n; i++) {
    pair<double, double> stop_loc = make_pair(distrib(gen), distrib(gen));
    if (i > 0)
      dist = space.d(stop_loc, stop.location);

    arrtime = arrtime + dist;
    auto req_ptr = make_shared<TransportationRequest<R2loc>>(
        i, 0, make_pair(0, 0), make_pair(0, 1), 0, inf, 0, inf);

    stop = {stop_loc, req_ptr, StopAction::internal, arrtime, 0, 0, inf};

    stoplist.push_back(stop);
  }
  // debug
  std::cout << "begin debug:" << std::endl;
  std::cout << stoplist[0].estimated_arrival_time << std::endl;
  stoplist[0].estimated_arrival_time = 8.4362;
  std::cout << stoplist[0].estimated_arrival_time << std::endl;

  // create new request
  R2loc req_origin = make_pair(distrib(gen), distrib(gen));
  R2loc req_dest = make_pair(distrib(gen), distrib(gen));

  auto request_ptr = make_shared<TransportationRequest<R2loc>>(
      42, 1, req_origin, req_dest, 0, inf, 0, inf);


  VehicleState<R2loc> vs {1, stoplist, space, "brute_force", 8};
  auto sz = vs.stoplist->size();
  auto [events, sl] = vs.fast_forward_time(500);
  auto sz2 = vs.stoplist->size();

  auto [vid, stuff] = vs.handle_transportation_request_single_vehicle(request_ptr);
  1 ==1 ;
}


TEST(RidepyTest, unittest) {
  Manhattan2D space;
  auto r1 = make_shared<TransportationRequest<R2loc>>(1, 0, make_pair(-100, 0),
                                                      make_pair(-100, 20));

  auto r2 = make_shared<TransportationRequest<R2loc>>(1, 0, make_pair(100, 10),
                                                      make_pair(100, 40));
  auto r3 = make_shared<TransportationRequest<R2loc>>(1, 0, make_pair(-100, 5),
                                                      make_pair(-100, 60));

  auto ir1 = make_shared<InternalRequest<R2loc>>(99, 0, make_pair(-100, 0));
  auto ir2 = make_shared<InternalRequest<R2loc>>(99, 0, make_pair(100, 0));

  vector<Stop<R2loc>> sl1_orig{
      Stop<R2loc>(ir1->location, ir1, StopAction::internal, 0, 0, 0, inf),
      Stop<R2loc>(r1->origin, r1, StopAction::pickup, 0, 1, 0, inf),
      Stop<R2loc>(r2->origin, r2, StopAction::pickup, 0, 2, 0, inf),
      Stop<R2loc>(r1->destination, r1, StopAction::dropoff, 0, 1, 0, inf),
      Stop<R2loc>(r2->destination, r2, StopAction::dropoff, 0, 0, 0, inf),
  };

  vector<Stop<R2loc>> sl2_orig{
      Stop<R2loc>(ir2->location, ir2, StopAction::internal, 0, 0, 0, inf),
      Stop<R2loc>(r3->origin, r3, StopAction::pickup, 0, 1, 0, inf),
      Stop<R2loc>(r3->destination, r3, StopAction::dropoff, 0, 0, 0, inf),
  };

  vector<int> capacities{10, 10};
  vector<vector<Stop<R2loc>>> old_stoplists{sl1_orig, sl2_orig};
  auto foo = 42;
}

TEST(RidepyTest, test_insertion_to_empty) {
  Manhattan2D space;
  auto r1 = make_shared<TransportationRequest<R2loc>>(
      42, 1.0, make_pair(0.0, 1.0), make_pair(0.0, 2.0), 0.0, INFINITY, 0.0,
      INFINITY);

  vector<Stop<R2loc>> sl1_orig{
      Stop<R2loc>(make_pair(0.0, 0.0), r1, StopAction::internal, 0.0, 0, 0,
                  INFINITY),
      Stop<R2loc>(make_pair(0.0, 1.0), r1, StopAction::pickup, 1.0, 1, 0,
                  INFINITY),
      Stop<R2loc>(make_pair(0.0, 2.0), r1, StopAction::dropoff, 1.0, 0, 0,
                  INFINITY),
  };

  vector<int> capacities{10};
  vector<vector<Stop<R2loc>>> old_stoplists{sl1_orig};
  auto foo = 42;
}
