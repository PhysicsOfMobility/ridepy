#include <string>
#include <iostream>
#include <tuple>
#include "data_structures.h"

using namespace std::literals::string_literals;

namespace cstates{
    class CRequest{
    public:
        std::string request_id;
        float creation_timestamp;
        CRequest(std::string request_id, float creation_timestamp):
            request_id{request_id},
            creation_timestamp{creation_timestamp}
            {
                FooBar test {"hello"s, 42};
            };
        CRequest(): request_id{""s}, creation_timestamp{0}{};
    };

    enum CStopAction{
        pickup = 1,
        dropoff = 2,
        internal = 3,
    };

    class CStop{
    public:
        std::tuple<float,float> location;
        const CRequest crequest;
        float estimated_arrival_time;
        float time_window_min;
        float time_window_max;
        CStopAction stop_action;

        CStop(
            std::tuple<float,float> location,
            CRequest crequest,
            float estimated_arrival_time,
            float time_window_min,
            float time_window_max,
            CStopAction stop_action
            ):
                location{location},
                crequest{crequest},
                estimated_arrival_time{estimated_arrival_time},
                time_window_min{time_window_min},
                time_window_max{time_window_max}{};
    };
} // end ns cstate


//namespace main{
//VehicleState::VehicleState(string vehicle_id, vector<CStop> stoplist){



//}



