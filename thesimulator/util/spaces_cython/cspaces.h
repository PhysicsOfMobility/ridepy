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
#include <random>
#include <chrono> // for benchmarking
#include <iostream>

using namespace std;

namespace cstuff {
    typedef pair<double, double> R2loc;

    template<typename Loc>
    class TransportSpace {
    public:
        double velocity;

        virtual double d(Loc u, Loc v)=0;
        virtual double t(Loc u, Loc v)=0;
        virtual pair<Loc, double> interp_dist(Loc u, Loc v, double dist_to_dest)=0;
        virtual pair<Loc, double> interp_time(Loc u, Loc v, double time_to_dest)=0;

        TransportSpace():velocity{1}{};
        TransportSpace(double velocity):velocity{velocity}{};
        virtual ~TransportSpace(){};
    };


    class Euclidean2D: public TransportSpace<R2loc> {
    public:
        double d(R2loc u, R2loc v) override;
        double t(R2loc u, R2loc v) override;
        pair<R2loc, double> interp_dist(R2loc u, R2loc v, double dist_to_dest) override;
        pair<R2loc, double> interp_time(R2loc u, R2loc v, double time_to_dest) override;

        Euclidean2D();
        Euclidean2D(double);
    };

    class Manhattan2D: public TransportSpace<R2loc> {
    public:
        double d(R2loc u, R2loc v) override;
        double t(R2loc u, R2loc v) override;
        pair<R2loc, double> interp_dist(R2loc u, R2loc v, double dist_to_dest) override;
        pair<R2loc, double> interp_time(R2loc u, R2loc v, double time_to_dest) override;

        Manhattan2D();
        Manhattan2D(double);
    };

}

#endif
//THESIMULATOR_CSPACES_H