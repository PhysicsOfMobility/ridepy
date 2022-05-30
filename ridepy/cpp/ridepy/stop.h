#ifndef RIDEPY_CPP_STOP_H
#define RIDEPY_CPP_STOP_H

#include "request.h"
#include "timewindow.h"

namespace ridepy {

enum class StopAction {
    PICKUP   = 0,
    DROPOFF  = 1,
    INTERNAL = 2
};

template <typename Loc>
struct Stop{
    Loc location;
    Request *request;
    StopAction action = StopAction::INTERNAL;
    double estimated_arrival_time = 0.;
    int occupancy_after_servicing = 0;
    TimeWindow time_window;

    Stop() {}
    Stop(const Loc &location, Request *request = Request(-1,0), const StopAction action = StopAction::INTERNAL,
         const double estimated_arrival_time = 0., const int occupancy_after_servicing = 0, const TimeWindow time_window = TimeWindow())
        : location(location), request(request), action(action),
          estimated_arrival_time(estimated_arrival_time), occupancy_after_servicing(occupancy_after_servicing), time_window(time_window)
    {}
};

struct StopEvent{
    StopAction action;
    int request_id;
    int vehicle_id;
    double timestamp;
};

} // namespace ridepy

#endif // RIDEPY_CPP_STOP_H
