#ifndef RIDEPY_CPP_REQUEST_H
#define RIDEPY_CPP_REQUEST_H

namespace ridepy {

struct Request{
    int    request_id;
    double creation_timestamp;

    inline Request(const int request_id, const double creation_timestamp)
        : request_id(request_id), creation_timestamp(creation_timestamp)
    {}
};

} // namespace ridepy

#endif // RIDEPY_CPP_REQUEST_H
