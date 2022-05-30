#ifndef RIDEPY_CPP_TRANSPORTATIONREQUEST_H
#define RIDEPY_CPP_TRANSPORTATIONREQUEST_H

#include <cmath>

#include "request.h"
#include "timewindow.h"

namespace ridepy {

template <typename Loc>
struct TransportationRequest : public Request{
    Loc origin;
    Loc destination;
    TimeWindow pickup_timewindow;
    TimeWindow delivery_timewindow;

    inline TransportationRequest(const int request_id, const double creation_timestamp, const Loc &origin, const Loc &destination,
                                 const TimeWindow &pickup_timewindow = TimeWindow(), const TimeWindow &delivery_timewindow = TimeWindow())
        : Request(request_id,creation_timestamp), origin(origin), destination(destination)
        , pickup_timewindow(pickup_timewindow), delivery_timewindow(delivery_timewindow)
    {}
};

} // namespace ridepy


#endif // RIDEPY_CPP_TRANSPORTATIONREQUEST_H
