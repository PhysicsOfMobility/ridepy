#ifndef INSERTIONRESULT_H
#define INSERTIONRESULT_H

#include <deque>

#include "timewindow.h"
#include "stop.h"
#include "singlevehiclesolution.h"

namespace ridepy {

template <typename Loc>
struct InsertionResult{
    std::deque<Stop<Loc>> new_stoplist;
    double min_cost = 0;
    TimeWindow pickup_window;
    TimeWindow dropoff_window;

    InsertionResult(const std::deque<Stop<Loc>> new_stoplist = {}, const double min_cost = INFINITY,
                    const TimeWindow &pickup_window = TimeWindow(INFINITY,INFINITY), const TimeWindow &dropoff_window = TimeWindow(INFINITY,INFINITY))
        : new_stoplist(new_stoplist), min_cost(min_cost), pickup_window(pickup_window), dropoff_window(dropoff_window)
    {}

    SingleVehicleSolution toSingleVehicleSolution(const int vehicle_id){
        return SingleVehicleSolution(vehicle_id,min_cost,pickup_window,dropoff_window);
    }
};

} // namespace ridepy

#endif // INSERTIONRESULT_H
