#ifndef RIDEPY_CPP_TIMEWINDOW_H
#define RIDEPY_CPP_TIMEWINDOW_H

#include <cmath>

namespace ridepy {

struct TimeWindow{
    double min;
    double max;

    inline TimeWindow(const double min = 0, const double max = INFINITY)
        : min(min), max(max)
    {}
};

} // namespace ridepy

#endif // RIDEPY_CPP_TIMEWINDOW_H
