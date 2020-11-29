
#include "cstuff.h"


using namespace std;

namespace cstuff{

double Euclidean2D::d(R2loc u, R2loc v) const
{
    return sqrt((u.first-v.first)*(u.first-v.first) + (u.second-v.second)*(u.second-v.second));
}

Euclidean2D::Euclidean2D() = default;

Request::Request() = default;
Request::Request(
    int request_id,
    double creation_timestamp,
    R2loc origin,
    R2loc destination,
    double pickup_timewindow_min,
    double pickup_timewindow_max,
    double delivery_timewindow_min,
    double delivery_timewindow_max
    ):
        request_id{request_id},
        creation_timestamp{creation_timestamp},
        origin{origin},
        destination{destination},
        pickup_timewindow_min{pickup_timewindow_min},
        pickup_timewindow_max{pickup_timewindow_max},
        delivery_timewindow_min{delivery_timewindow_min},
        delivery_timewindow_max{delivery_timewindow_max}{};


Stop::Stop()=default;
Stop::Stop(
    R2loc loc, Request req, StopAction action, double estimated_arrival_time,
    double time_window_min, double time_window_max):
        location{loc},
        request{req},
        action{action},
        estimated_arrival_time{estimated_arrival_time},
        time_window_min{time_window_min},
        time_window_max{time_window_max}{};
double Stop::estimated_departure_time(){
        return max(estimated_arrival_time, time_window_min);
    };


Stoplist insert_request_to_stoplist_drive_first(
        Stoplist& stoplist,
        const Request& request,
        int pickup_idx,
        int dropoff_idx,
        const Euclidean2D& space
){
    /*
    Inserts a request into  a stoplist. The pickup(dropoff) is inserted after pickup(dropoff)_idx.
    The estimated arrival times at all the stops are updated assuming a drive-first strategy.
    */

    // We don't want to modify stoplist in place. Make a copy.
    Stoplist new_stoplist{stoplist}; // TODO: NEED TO copy?
    // Handle the pickup
    auto stop_before_pickup = new_stoplist[pickup_idx];
    auto cpat_at_pu = stop_before_pickup.estimated_departure_time() + space.d(
        stop_before_pickup.location, request.origin
    );
    Stop pickup_stop(request.origin, request, StopAction::pickup, cpat_at_pu, request.pickup_timewindow_min,
                     request.pickup_timewindow_max);

    insert_stop_to_stoplist_drive_first(new_stoplist, pickup_stop, pickup_idx, space);
    // Handle the dropoff
    dropoff_idx += 1;
    auto& stop_before_dropoff = new_stoplist[dropoff_idx];
    auto cpat_at_do = stop_before_dropoff.estimated_departure_time() + space.d(
        stop_before_dropoff.location, request.destination
    );
    Stop dropoff_stop(
        request.destination,
        request,
        StopAction::dropoff,
        cpat_at_do,
        request.delivery_timewindow_min,
        request.delivery_timewindow_max);
    insert_stop_to_stoplist_drive_first(new_stoplist, dropoff_stop, dropoff_idx, space);
    return new_stoplist;
    }


void insert_stop_to_stoplist_drive_first(
        Stoplist& stoplist,
        Stop& stop,
        int idx,
        const Euclidean2D& space
)
{
    /*
    Note: Modifies stoplist in-place. The passed stop has estimated_arrival_time set to None
    Args:
        stoplist:
        stop:
        idx:
        space:

    Returns:
    */
    auto& stop_before_insertion = stoplist[idx];
    // Stop later_stop
    // cdef double departure_previous_stop, cpat_next_stop,  delta_cpat_next_stop, old_departure, new_departure
    double distance_to_new_stop = space.d(stop_before_insertion.location, stop.location);
    double cpat_new_stop = cpat_of_inserted_stop(
        stop_before_insertion,
        distance_to_new_stop
    );
    stop.estimated_arrival_time = cpat_new_stop;
    if (idx < stoplist.size() - 1)
    {
        // update cpats of later stops
        auto departure_previous_stop = stop.estimated_departure_time();
        auto cpat_next_stop = departure_previous_stop + space.d(
            stop.location, stoplist[idx + 1].location
        );
        auto delta_cpat_next_stop = cpat_next_stop - stoplist[idx + 1].estimated_arrival_time;
//        BOOST_FOREACH(auto later_stop, boost::make_iterator_range(stoplist.begin()+idx + 1, stoplist.end()))
        for (auto later_stop = stoplist.begin()+idx + 1; later_stop !=stoplist.end(); ++later_stop)
        {
            auto old_departure = later_stop->estimated_departure_time();
            later_stop->estimated_arrival_time += delta_cpat_next_stop;
            auto new_departure = later_stop->estimated_departure_time();

            auto delta_cpat_next_stop = new_departure - old_departure;
            if (delta_cpat_next_stop == 0) break;
        }
    }
    stoplist.insert(stoplist.begin()+idx + 1, stop);
}

double cpat_of_inserted_stop(Stop& stop_before, double distance_from_stop_before)
{
    /*
    Note: Assumes drive first strategy.
    Args:
        stop_before:
        distance_from_stop_before:

    Returns:

    */
    return stop_before.estimated_departure_time() + distance_from_stop_before;
}

double distance_to_stop_after_insertion(
        const Stoplist &stoplist, const R2loc location, int index, const Euclidean2D& space
)
{
    // note that index is there the new stop will be inserted. So index+1 is where the next stop is
    if (index < stoplist.size() - 1) return space.d(location, stoplist[index].location);
    else return 0;
}

double distance_from_current_stop_to_next(
        const Stoplist &stoplist, int i, const Euclidean2D& space
)
{
        if (i < stoplist.size() - 1) return space.d(stoplist[i].location, stoplist[i + 1].location);
        else return 0;
}

int is_timewindow_violated_dueto_insertion(
        const Stoplist& stoplist, int idx, double est_arrival_first_stop_after_insertion
)
{
    /*
    Assumes drive first strategy.
    Args:
        stoplist:
        idx:
        est_arrival_first_stop_after_insertion:

    Returns:

    */
    // double delta_cpat, old_leeway, new_leeway, old_departure, new_departure
    if (idx >= stoplist.size() - 1) return false;
    auto delta_cpat = (
        est_arrival_first_stop_after_insertion
        - stoplist[idx].estimated_arrival_time
    );
//    BOOST_FOREACH(auto& stop, boost::make_iterator_range(stoplist.begin()+idx, stoplist.end()))
    for (auto stop=stoplist.begin()+idx; stop != stoplist.end(); ++stop)
    {
        auto old_leeway = stop->time_window_max - stop->estimated_arrival_time;
        auto new_leeway = old_leeway - delta_cpat;

        if ((new_leeway < 0) & (0<= old_leeway)) return true;
        else
        {
            auto old_departure = max(stop->time_window_min, stop->estimated_arrival_time);
            auto new_departure = max(
                stop->time_window_min, stop->estimated_arrival_time + delta_cpat
            );
            auto delta_cpat = new_departure - old_departure;
            if (delta_cpat == 0)
            {
                // no need to check next stops
                return false;
            }
        }
    }
    return false;
}

InsertionResult brute_force_distance_minimizing_dispatcher(
        const Request& request,
        Stoplist& stoplist,
        const Euclidean2D& space
)
{
    /*
    Dispatcher that maps a vehicle's stoplist and a request to a new stoplist
    by minimizing the total driving distance.

    Parameters
    ----------
    request
        request to be serviced
    stoplist
        stoplist of the vehicle, to be mapped to a new stoplist
    space
        transport space the vehicle is operating on

    Returns
    -------

    */
    double min_cost = INFINITY;

    // Warning: i,j refers to the indices where the new stop would be inserted. So i-1/j-1 is the index of
    // the stop preceeding the stop to be inserted.
    pair<int, int> best_insertion {0, 0};
    int i = 0;
    for (auto& stop_before_pickup: stoplist)
    {
        i++; // The first iteration of the loop: i =1 (new stop would be inserted at idx=1). Insertion at 0 impossible.
        auto distance_to_pickup = space.d(stop_before_pickup.location, request.origin);
        auto CPAT_pu = cpat_of_inserted_stop(stop_before_pickup, distance_to_pickup);
        // check for request's pickup timewindow violation
        if (CPAT_pu > request.pickup_timewindow_max) continue;
        auto EAST_pu = request.pickup_timewindow_min;

        // dropoff immediately
        auto CPAT_do = max(EAST_pu, CPAT_pu) + space.d(request.origin, request.destination);
        auto EAST_do = request.delivery_timewindow_min;
        // check for request's dropoff timewindow violation
        if (CPAT_do > request.delivery_timewindow_max) continue;
        // compute the cost function
        auto distance_to_dropoff = space.d(request.origin, request.destination);
        auto distance_from_dropoff = distance_to_stop_after_insertion(
            stoplist, request.destination, i, space
        );

        auto original_pickup_edge_length = distance_from_current_stop_to_next(
            stoplist, i-1, space
        );
        auto total_cost = (
            distance_to_pickup
            + distance_to_dropoff
            + distance_from_dropoff
            - original_pickup_edge_length
        );
        if (total_cost < min_cost)
        {
            // check for constraint violations at later points
            auto cpat_at_next_stop =
                max(CPAT_do, request.delivery_timewindow_min) + distance_from_dropoff;
            if (~ is_timewindow_violated_dueto_insertion(
                stoplist, i, cpat_at_next_stop))
            {
                best_insertion = {i, i};
                min_cost = total_cost;
            }
        }
        // Try dropoff not immediately after pickup
        auto distance_from_pickup = distance_to_stop_after_insertion(
            stoplist, request.origin, i, space);
        auto cpat_at_next_stop = (
            max(CPAT_pu, request.pickup_timewindow_min) + distance_from_pickup
        );
        if (is_timewindow_violated_dueto_insertion(stoplist, i, cpat_at_next_stop)) continue;
        auto pickup_cost = (
            distance_to_pickup + distance_from_pickup - original_pickup_edge_length
        );
        int j = i;
//        BOOST_FOREACH(auto stop_before_dropoff, boost::make_iterator_range(stoplist.begin()+i, stoplist.end()))
        for (auto stop_before_dropoff=stoplist.begin()+i; stop_before_dropoff != stoplist.end(); ++stop_before_dropoff)
        {
            j++;
            distance_to_dropoff = space.d(
                stop_before_dropoff->location, request.destination
            );
            CPAT_do = cpat_of_inserted_stop(
                *stop_before_dropoff,
                +distance_to_dropoff
            );
            if (CPAT_do > request.delivery_timewindow_max) continue;
            distance_from_dropoff = distance_to_stop_after_insertion(
                stoplist, request.destination, j, space
            );
            auto original_dropoff_edge_length = distance_from_current_stop_to_next(
                stoplist, j-1, space
            );
            auto dropoff_cost = (
                distance_to_dropoff
                + distance_from_dropoff
                - original_dropoff_edge_length
            );

            total_cost = pickup_cost + dropoff_cost;
            if (total_cost > min_cost) continue;
            else
            {
                // cost has decreased. check for constraint violations at later stops
                cpat_at_next_stop = (
                    max(CPAT_do, request.delivery_timewindow_min)
                    + distance_from_dropoff
                );
                if (~ is_timewindow_violated_dueto_insertion(
                    stoplist, j, cpat_at_next_stop))
                {
                    best_insertion = {i, j};
                    min_cost = total_cost;
                }
            }
        }
    }
    int best_pickup_idx = best_insertion.first;
    int best_dropoff_idx = best_insertion.second;
    auto new_stoplist = insert_request_to_stoplist_drive_first(
        stoplist,
        request,
        best_pickup_idx,
        best_dropoff_idx,
        space
    );
    std::cout<<"Best insertion: "<<best_pickup_idx << ", " <<best_dropoff_idx<<std::endl;
    auto EAST_pu = new_stoplist[best_pickup_idx + 1].time_window_min;
    auto LAST_pu = new_stoplist[best_pickup_idx + 1].time_window_max;

    auto EAST_do = new_stoplist[best_dropoff_idx + 2].time_window_min;
    auto LAST_do = new_stoplist[best_dropoff_idx + 2].time_window_max;
    return InsertionResult {new_stoplist, min_cost, EAST_pu, LAST_pu, EAST_do, LAST_do};
}
}// end ns cstuff


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
    R2loc a, b;
    for (int i=0; i<n; i++)
    {
        R2loc stop_loc = make_pair(distrib(gen), distrib(gen));
        if (i>0) dist = space.d(stop_loc, stop.location);

        arrtime = arrtime + dist;
        Request dummy_req {i, 0, make_pair(0,0), make_pair(0,1), 0, INFINITY, 0, INFINITY};
        stop = {stop_loc, dummy_req, StopAction::internal, arrtime, 0, INFINITY};

        stoplist.push_back(stop);
    }
    // create new request
    R2loc req_origin = make_pair(distrib(gen), distrib(gen));
    R2loc req_dest = make_pair(distrib(gen), distrib(gen));
    Request request {42, 1, req_origin, req_dest, 0, INFINITY, 0, INFINITY};

    auto start = std::chrono::system_clock::now();
    auto x = brute_force_distance_minimizing_dispatcher(request, stoplist, space);
    auto end = std::chrono::system_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    std::cout << "Time taken: " << elapsed.count() << " s" << std::endl;
    std::cout << x.min_cost << endl;
}