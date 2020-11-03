#include <string>
#include <iostream>
#include <tuple>

namespace cstate{
    class CRequest{
    public:
        const std::string request_id;
        const float creation_timestamp;
        CRequest(std::string request_id, float creation_timestamp):
            request_id(request_id),
            creation_timestamp(creation_timestamp){};
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
                location(location),
                crequest(crequest),
                estimated_arrival_time(estimated_arrival_time),
                time_window_min(time_window_min),
                time_window_max(time_window_max){};
    };
} // end ns cstate

int main(){
    cstate::CRequest req("foo", 0.12);
    std::cout<<"Request: "<<req.request_id<<std::endl;
    cstate::CStop stop(std::make_tuple(0,0), req, 0,0,0, cstate::CStopAction::pickup);
    std::cout<<"Stop: "<<std::get<0>(stop.location)<<std::endl;
}


//namespace main{
//VehicleState::VehicleState(string vehicle_id, vector<CStop> stoplist){



//}



