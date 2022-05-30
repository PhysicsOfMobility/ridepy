#ifndef RIDEPY_CPP_INTERNALREQUEST_H
#define RIDEPY_CPP_INTERNALREQUEST_H

#include "request.h"

namespace ridepy {

template <typename Loc>
struct InternalRequest : public Request{
    Loc location;

    InternalRequest(const int request_id,const double creation_timestamp, const Loc &location)
        : request_id(request_id), creation_timestamp(creation_timestamp), location(location)
    {}
};

} // namespace ridepy

#endif // RIDEPY_CPP_INTERNALREQUEST_H
