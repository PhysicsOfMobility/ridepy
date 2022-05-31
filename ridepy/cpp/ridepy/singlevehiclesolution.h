#ifndef SINGLEVEHICLESOLUTION_H
#define SINGLEVEHICLESOLUTION_H

#include <vector>

#include "timewindow.h"
#include "stop.h"

namespace ridepy {

struct SingleVehicleSolution{
    int vehicle_id = -1;
    double min_cost = 0;
    TimeWindow pickup_window;
    TimeWindow dropoff_window;

    SingleVehicleSolution(const int vehicle_id, const double min_cost, const TimeWindow &pickup_window, const TimeWindow &dropoff_window)
        : vehicle_id(vehicle_id), min_cost(min_cost), pickup_window(pickup_window), dropoff_window(dropoff_window)
    {}
};

} // namespace ridepy

#endif // SINGLEVEHICLESOLUTION_H
