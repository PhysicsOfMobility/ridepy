from thesimulator.cdata_structures import (
    TransportationRequest,
    InternalRequest,
    Stop,
    StopAction,
    Stoplist,
)
from thesimulator.cdata_structures import LocType

import pytest

from numpy.testing import assert_array_almost_equal, assert_array_equal
from numpy import inf
from copy import deepcopy


def test_attr_not_none():
    """
    Failing test added to demonstrate that there's a problem with with creating cython
    objects from existing pointers and garbage collection.
    """
    ir = InternalRequest(999, 0, (0, 0))
    s0 = Stop((0, 0), ir, StopAction.internal, 0, 0, 0)
    sl = Stoplist([s0], LocType.R2LOC)
    assert sl[0].request is not None


@pytest.fixture
def r0():
    return InternalRequest(request_id=999, creation_timestamp=7.89, location=(1, 3))


@pytest.fixture
def r1():
    return TransportationRequest(
        request_id=7,
        creation_timestamp=1.8,
        origin=(3, 7),
        destination=(2, 1),
        pickup_timewindow_min=2.13,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=4.24,
        delivery_timewindow_max=inf,
    )


@pytest.fixture
def r2():
    return TransportationRequest(
        request_id=8,
        creation_timestamp=2,
        origin=(4, 1),
        destination=(3, 7),
        pickup_timewindow_min=0,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=0,
        delivery_timewindow_max=inf,
    )


@pytest.fixture
def s0(r0):
    return Stop(
        location=r0.location,
        request=r0,
        action=StopAction.internal,
        estimated_arrival_time=3.67,
        time_window_min=9.12,
        time_window_max=inf,
    )


@pytest.fixture
def s1(r1):
    return Stop(
        location=r1.origin,
        request=r1,
        action=StopAction.pickup,
        estimated_arrival_time=2.51,
        time_window_min=inf,
        time_window_max=9.13,
    )


@pytest.fixture
def s2(r2):
    return Stop(
        location=r2.origin,
        request=r2,
        action=StopAction.pickup,
        estimated_arrival_time=3.86,
        time_window_min=1,
        time_window_max=inf,
    )


@pytest.fixture
def s3(r1):
    return Stop(
        location=r1.destination,
        request=r1,
        action=StopAction.dropoff,
        estimated_arrival_time=2.17,
        time_window_min=1,
        time_window_max=inf,
    )


@pytest.fixture
def s4(r2):
    return Stop(
        location=r2.destination,
        request=r2,
        action=StopAction.dropoff,
        estimated_arrival_time=7.16,
        time_window_min=1,
        time_window_max=inf,
    )


@pytest.fixture
def stoplist(s0, s1, s2, s3, s4):
    return Stoplist([s0, s1, s2, s3, s4], LocType.R2LOC)


def test_attr_get():
    # test internal requests
    r0 = InternalRequest(request_id=999, creation_timestamp=7.89, location=(1, 3))

    assert_array_equal(r0.request_id, 999)
    assert_array_equal(r0.location, (1, 3))
    assert_array_almost_equal(r0.creation_timestamp, 7.89)

    # test transportation requests
    r1 = TransportationRequest(
        request_id=7,
        creation_timestamp=1.8,
        origin=(3, 7),
        destination=(2, 1),
        pickup_timewindow_min=2.13,
        pickup_timewindow_max=inf,
        delivery_timewindow_min=4.24,
        delivery_timewindow_max=inf,
    )

    assert_array_equal(r1.request_id, 7)
    # assert_array_equal(r1.creation_timestamp, 1.8)
    assert_array_equal(r1.origin, (3, 7))
    assert_array_equal(r1.destination, (2, 1))
    assert_array_equal(r1.pickup_timewindow_min, 2.13)
    assert_array_equal(r1.pickup_timewindow_max, inf)
    assert_array_equal(r1.delivery_timewindow_min, 4.24)
    assert_array_equal(r1.delivery_timewindow_max, inf)

    # test stops holding internal requests
    s0 = Stop(
        location=r0.location,
        request=r0,
        action=StopAction.internal,
        estimated_arrival_time=3.67,
        time_window_min=9.12,
        time_window_max=inf,
    )
    assert_array_equal(s0.location, (1, 3))
    assert s0.request == r0
    assert s0.action == StopAction.internal
    assert_array_equal(s0.estimated_arrival_time, 3.67)
    assert_array_equal(s0.time_window_min, 9.12)
    assert_array_equal(s0.time_window_max, inf)

    # test stops holding transportation requests
    s1 = Stop(
        location=r1.origin,
        request=r1,
        action=StopAction.pickup,
        estimated_arrival_time=2.51,
        time_window_min=inf,
        time_window_max=9.13,
    )
    assert_array_equal(s1.location, (3, 7))
    assert s1.request == r1
    assert s1.action == StopAction.pickup
    assert_array_equal(s1.estimated_arrival_time, 2.51)
    assert_array_equal(s1.time_window_min, inf)
    assert_array_equal(s1.time_window_max, 9.13)


def test_attr_get_stoplist(r0, r1, r2, s0, s1, s2, s3, s4, stoplist):
    assert len(stoplist) == 5
    assert_array_almost_equal(
        [s.request.request_id for s in stoplist], [999, 7, 8, 7, 8]
    )
    assert_array_almost_equal(
        [s.request.creation_timestamp for s in stoplist], [7.89, 1.8, 2, 1.8, 2]
    )
    assert_array_almost_equal(
        [s.estimated_arrival_time for s in stoplist], [3.67, 2.51, 3.86, 2.17, 7.16]
    )


def test_attr_set_intern_req(r0):
    # test internal requests
    r0.location = (5, 1)
    assert_array_equal(r0.location, (5, 1))


def test_attr_set_transp_req(r1):
    # test transportation requests
    r1.origin = (9, 2)
    assert_array_equal(r1.origin, (9, 2))
    r1.destination = (8, 3)
    assert_array_equal(r1.destination, (8, 3))
    r1.pickup_timewindow_min = 8.1683
    assert_array_equal(r1.pickup_timewindow_min, 8.1683)
    r1.pickup_timewindow_max = 4.8924
    assert_array_equal(r1.pickup_timewindow_max, 4.8924)
    r1.delivery_timewindow_min = 7.3628
    assert_array_equal(r1.delivery_timewindow_min, 7.3628)
    r1.delivery_timewindow_max = 2.8946
    assert_array_equal(r1.delivery_timewindow_max, 2.8946)


def test_attr_set_stop_with_intern_req(s0):
    # test stops holding internal requests
    s0.location = (89, 23)
    assert_array_equal(s0.location, (89, 23))
    s0.estimated_arrival_time = 5.7812
    assert_array_equal(s0.estimated_arrival_time, 5.7812)

    # test setting attributes of the request object inside
    s0.request.location = (54, 91)
    assert s0.request.location == (54, 91)


def test_attr_set_stop_with_transp_req(s1):
    # test stops holding transportation requests
    s1.location = (92, 54)
    assert_array_equal(s1.location, (92, 54))
    s1.estimated_arrival_time = 4.1957
    assert_array_equal(s1.estimated_arrival_time, 4.1957)

    # test setting attributes of the request object inside
    s1.request.origin = (89, 12)
    assert_array_equal(s1.request.origin, (89, 12))
    s1.request.destination = (61, 39)
    assert_array_equal(s1.request.destination, (61, 39))
    s1.request.pickup_timewindow_min = 8.4913
    assert_array_equal(s1.request.pickup_timewindow_min, 8.4913)
    s1.request.pickup_timewindow_max = 1.9258
    assert_array_equal(s1.request.pickup_timewindow_max, 1.9258)
    s1.request.delivery_timewindow_min = 6.6678
    assert_array_equal(s1.request.delivery_timewindow_min, 6.6678)
    s1.request.delivery_timewindow_max = 4.4412
    assert_array_equal(s1.request.delivery_timewindow_max, 4.4412)


def test_attr_set_stoplist(stoplist):
    stoplist[0].location = (92, 54)
    assert_array_equal(stoplist[0].location, (92, 54))
    stoplist[0].estimated_arrival_time = 4.1957
    assert_array_equal(stoplist[0].estimated_arrival_time, 4.1957)

    # test setting attributes of the request object inside
    stoplist[3].request.origin = (12, 83)
    assert_array_equal(stoplist[3].request.origin, (12, 83))
    stoplist[3].request.destination = (9, 71)
    assert_array_equal(stoplist[3].request.destination, (9, 71))
    stoplist[3].request.pickup_timewindow_min = 67.131
    assert_array_equal(stoplist[3].request.pickup_timewindow_min, 67.131)
    stoplist[3].request.pickup_timewindow_max = 48.581
    assert_array_equal(stoplist[3].request.pickup_timewindow_max, 48.581)
    stoplist[3].request.delivery_timewindow_min = 33.112
    assert_array_equal(stoplist[3].request.delivery_timewindow_min, 33.112)
    stoplist[3].request.delivery_timewindow_max = 54.831
    assert_array_equal(stoplist[3].request.delivery_timewindow_max, 54.831)


@pytest.mark.xfail(
    reason="Stoplist.__getitem__ returns a wrapper around &self.ustoplist._stoplist_r2loc[i]"
)
def test_stoplist_getitem_and_elem_removal_consistent(stoplist):
    """
    s3 points to the 3rd member of stoplist. After removing the second element, s3 will point to the previous element,
    failing this test.
    """
    s3 = stoplist[3]
    assert s3.request.request_id == 7
    assert_array_almost_equal(s3.request.pickup_timewindow_min, 2.13)
    assert_array_almost_equal(s3.estimated_arrival_time, 2.17)

    stoplist.remove_nth_elem(2)
    assert s3.request.request_id == 7
    assert_array_almost_equal(s3.request.pickup_timewindow_min, 2.13)
    assert_array_almost_equal(s3.estimated_arrival_time, 2.17)


def test_stoplist_getitem_and_elem_removal_consistent_with_deepcopy(stoplist):
    """
    But with a deepcopy, the problem with the failing test test_stoplist_getitem_and_elem_removal_consistent
    doesn't occur.
    """
    s3 = deepcopy(stoplist[3])
    assert s3.request.request_id == 7
    assert_array_almost_equal(s3.request.pickup_timewindow_min, 2.13)
    assert_array_almost_equal(s3.estimated_arrival_time, 2.17)

    stoplist.remove_nth_elem(2)
    assert s3.request.request_id == 7
    assert_array_almost_equal(s3.request.pickup_timewindow_min, 2.13)
    assert_array_almost_equal(s3.estimated_arrival_time, 2.17)
