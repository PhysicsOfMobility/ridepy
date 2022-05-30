#ifndef INSERTIONRESULT_H
#define INSERTIONRESULT_H

#include <vector>

#include "timewindow.h"
#include "stop.h"
#include "singlevehiclesolution.h"

namespace ridepy {

template <typename Loc>
struct InsertionResult{
    std::vector<Stop<Loc>> new_stoplist;
    double min_cost = 0;
    TimeWindow pickup_window;
    TimeWindow dropoff_window;

    SingleVehicleSolution toSingleVehicleSolution(const int vehicle_id){
        return SingleVehicleSolution(vehicle_id,min_cost,pickup_window,dropoff_window);
    }
};

} // namespace ridepy

#endif // INSERTIONRESULT_H
