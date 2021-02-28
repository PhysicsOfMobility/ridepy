from thesimulator.cdata_structures import TransportationRequest, InternalRequest, Stop, StopAction, Stoplist
from thesimulator.cdata_structures import LocType


def test_attr_none():
    """
    Failing test added to demonstrate that there's a problem with with creating cython
    objects from existing pointers and garbage collection.
    """
    ir = InternalRequest(999, 0, (0, 0))
    s0 = Stop((0, 0), ir, StopAction.internal, 0, 0, 0)
    sl = Stoplist([s0], LocType.R2LOC)
    assert sl[0].request is not None


def test_attr_get():
    # check also doing it in a nested manner, e.g.
    # stoplist[0].request.request_id = "foo"
    assert False

def test_attr_set():
    assert False