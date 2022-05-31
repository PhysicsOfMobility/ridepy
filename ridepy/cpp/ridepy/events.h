#ifndef EVENTS_H
#define EVENTS_H

#include <string>

#include "request.h"
#include "timewindow.h"

namespace ridepy{

enum class EventType{
    EVENT,
    STOP_EVENT,
    REQUEST_EVENT,
    REQUESTOFFERING_EVENT,
    REQUESTREJECTION_EVENT
};

/*!
 * \brief The base structure all events in RidePy inherit from: Each event has to provide an EventType and a timestamp.
 */
struct Event{
    EventType type;
    double timestamp;

    Event(EventType type = EventType::EVENT, double timestamp = 0)
        : type(type), timestamp(timestamp)
    {}
};

/*!
 * \brief The base structure for all events related to requests. These events has to provide in addition to a \p type_name and a \p timestamp a \p requestId
 */
struct RequestEvent : public Event{
    int requestId;
    TimeWindow estimated_invehicle_time;
    std::string comment;

    RequestEvent(const EventType type = EventType::REQUEST_EVENT, const Request &request = {-1,0}, const TimeWindow estimated_invehicle_time = 0., const std::string &comment = "")
        : Event(type,request.creation_timestamp), requestId(request.request_id), estimated_invehicle_time(estimated_invehicle_time), comment(comment)
    {}
};

} // namespace ridepy

#endif // EVENTS_H
