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
};

} // namespace ridepy

#endif // SINGLEVEHICLESOLUTION_H
