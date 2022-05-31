#ifndef ABSTRACTDISPATCHER_H
#define ABSTRACTDISPATCHER_H

#include <deque>

#include "insertionresult.h"
#include "transportationrequest.h"
#include "transportspace.h"

namespace ridepy {

template <typename Loc>
class AbstractDispatcher
{
public:
    virtual InsertionResult<Loc> operator()(const TransportationRequest<Loc> &request, const std::deque<Stop<Loc>> &stoplist, TransportSpace<Loc> &space, int seat_capacity) = 0;
};

} // namespace ridepy

#endif // ABSTRACTDISPATCHER_H
