//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef THESIMULATOR_CDISPATCHERS_UTILS_H
#define THESIMULATOR_CDISPATCHERS_UTILS_H

#include "../../cdata_structures/cdata_structures.h"

namespace cstuff {
    std::vector<Stop> insert_request_to_stoplist_drive_first(
            std::vector<Stop> &stoplist,
            const Request &request,
            int pickup_idx,
            int dropoff_idx,
            const TransportSpace &space
    );

    void insert_stop_to_stoplist_drive_first(
            std::vector<Stop> &stoplist,
            Stop &stop,
            int idx,
            const TransportSpace &space
    );

    double cpat_of_inserted_stop(Stop &stop_before, double distance_from_stop_before);

    double distance_to_stop_after_insertion(
            const std::vector<Stop> &stoplist, const std::pair<double, double> location, int index,
            const TransportSpace &space
    );

    double distance_from_current_stop_to_next(
            const std::vector<Stop> &stoplist, int i, const TransportSpace &space
    );

    int is_timewindow_violated_dueto_insertion(
            const std::vector<Stop> &stoplist, int idx, double est_arrival_first_stop_after_insertion
    );
}


#endif //THESIMULATOR_CDISPATCHERS_UTILS_H
