#include "cspaces.h"


using namespace std;

namespace cstuff{

TransportSpace::TransportSpace():velocity{1}{};
TransportSpace::TransportSpace(double velocity):velocity{velocity}{};


Euclidean2D::Euclidean2D():TransportSpace{}{};
Euclidean2D::Euclidean2D(double velocity):TransportSpace{velocity}{};

double Euclidean2D::d(R2loc u, R2loc v) const
{
    return sqrt((u.first-v.first)*(u.first-v.first) + (u.second-v.second)*(u.second-v.second));
}

double Euclidean2D::t(R2loc u, R2loc v) const
{
    return this->d(u,v)/this->velocity;
}

pair<R2loc, double> Euclidean2D::interp_dist(R2loc u, R2loc v, double dist_to_dest) const
{
    double frac = dist_to_dest/this->d(u, v);
    return make_pair(
        R2loc {u.first*frac + (1-frac)*v.first, u.second*frac + (1-frac)*v.second}, 0);
}

pair<R2loc, double> Euclidean2D::interp_time(R2loc u, R2loc v, double time_to_dest) const
{
    double dist_to_dest = time_to_dest*(this->velocity);
    return this->interp_dist(u,v,dist_to_dest);
}

Manhattan2D::Manhattan2D():TransportSpace{}{};
Manhattan2D::Manhattan2D(double velocity):TransportSpace{velocity}{};

double Manhattan2D::d(R2loc u, R2loc v) const
{
    return std::abs(u.first-v.first) + std::abs(u.second-v.second);
}

double Manhattan2D::t(R2loc u, R2loc v) const
{
    return this->d(u,v)/this->velocity;
}

pair<R2loc, double> Manhattan2D::interp_dist(R2loc u, R2loc v, double dist_to_dest) const
{
    double dist = this->t(u, v);
    double sofar = dist - dist_to_dest;
    double dx = v.first - u.first;
    double dy = v.second - u.second;

    double x,y;

    if (sofar < std::abs(dx))
    {
        y = u.second;
        if (dx >0) x = u.first+sofar;
        else  x = u.first-sofar;
    }
    else
    {
        x = v.first;
        sofar -= std::abs(v.first-x);
        if (dy>0) y = u.second+sofar;
        else y = u.second-sofar;
    }

    return make_pair(
        R2loc {x,y}, 0);
}

pair<R2loc, double> Manhattan2D::interp_time(R2loc u, R2loc v, double time_to_dest) const
{
    double dist_to_dest = time_to_dest*(this->velocity);
    return this->interp_dist(u,v,dist_to_dest);
}
}//end ns cstuff


