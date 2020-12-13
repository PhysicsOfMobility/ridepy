//
// Created by Debsankha Manik on 13.12.20.
//

#ifndef THESIMULATOR_CDISPATCHERS_H
#define THESIMULATOR_CDISPATCHERS_H

#include "../cspaces/cspaces.h"
#include "../../cdata_structures/cdata_structures.h"
#include "cdispatchers_utils.h"

using namespace std;
namespace cstuff {
    InsertionResult
    brute_force_distance_minimizing_dispatcher(
            const Request &request,
            vector<Stop> &stoplist,
            const TransportSpace &space);

}
#endif //THESIMULATOR_CDISPATCHERS_H
