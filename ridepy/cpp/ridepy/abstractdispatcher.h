#ifndef ABSTRACTDISPATCHER_H
#define ABSTRACTDISPATCHER_H

#include <vector>

#include "insertionresult.h"
#include "transportationrequest.h"
#include "transportspace.h"

namespace ridepy {

template <typename Loc>
class AbstractDispatcher
{
public:
    virtual InsertionResult<Loc> operator()(TransportationRequest<Loc> &request, std::vector<Stop<Loc>> &stoplist, TransportSpace<Loc> *space, int seat_capacity,
                                            bool debug = false) = 0;
};

} // namespace ridepy

#endif // ABSTRACTDISPATCHER_H
