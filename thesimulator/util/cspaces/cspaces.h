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
    class TransportSpace {
    public:
        double velocity;

        double d(pair<double, double> u, pair<double, double> v) const;
        double t(pair<double, double> u, pair<double, double> v) const;
        pair<pair<double, double>, double> interp_dist(pair<double, double> u, pair<double, double> v, double dist_to_dest) const;
        pair<pair<double, double>, double> interp_time(pair<double, double> u, pair<double, double> v, double time_to_dest) const;

        TransportSpace();
        TransportSpace(double);
        virtual ~TransportSpace(){};
    };

    class Euclidean2D: public TransportSpace {
    public:
        double d(pair<double, double> u, pair<double, double> v) const ;
        double t(pair<double, double> u, pair<double, double> v) const ;
        pair<pair<double, double>, double> interp_dist(pair<double, double> u, pair<double, double> v, double dist_to_dest) const ;
        pair<pair<double, double>, double> interp_time(pair<double, double> u, pair<double, double> v, double time_to_dest) const ;

        Euclidean2D();
        Euclidean2D(double);
    };
}

#endif
//THESIMULATOR_CSPACES_H
