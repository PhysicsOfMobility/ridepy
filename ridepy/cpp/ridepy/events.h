#ifndef EVENTS_H
#define EVENTS_H

#include <string>

namespace ridepy{

enum class EventType{
    EVENT,
    STOP_EVENT,
    REQUEST_EVENT,
    REQUESTHANDLE_EVENT,
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
    double estimate;

    RequestEvent(const EventType type = EventType::REQUEST_EVENT, const double timestamp =0., const int requestId = 0, const double estimate = 0.)
        : Event(type,timestamp), requestId(requestId), estimate(estimate)
    {}
};

} // namespace ridepy

#endif // EVENTS_H
