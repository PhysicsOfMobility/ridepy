//
// Created by dmanik on 29.11.20.
//

#ifndef THESIMULATOR_CSPACES_H
#define THESIMULATOR_CSPACES_H

#include <utility> // for pair
#include <tuple>
#include <vector>
#include <algorithm>  // for max()
#include <cmath>
//#include <boost/foreach.hpp>
//#include <boost/range/iterator_range.hpp>
#include <random>
#include <chrono> // for benchmarking
#include <iostream>

using namespace std;

namespace cstuff {
    typedef pair<double, double> R2loc;

    class Euclidean2D {
    public:
        double velocity;

        double d(R2loc u, R2loc v) const;
        double t(R2loc u, R2loc v) const;
        pair<R2loc, double> interp_dist(R2loc u, R2loc v, double dist_to_dest) const;
        pair<R2loc, double> interp_time(R2loc u, R2loc v, double time_to_dest) const;

        Euclidean2D();
        Euclidean2D(double);
    };
}

#endif
//THESIMULATOR_CSPACES_H
