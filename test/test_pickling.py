from io import BytesIO
from numpy import inf
import pickle
import random

from ridepy import data_structures as pyds
from ridepy import data_structures_cython as cyds
from ridepy.util import spaces as pyspaces
from ridepy.util import spaces_cython as cyspaces
from ridepy.extras.spaces import make_nx_cycle_graph


def pickled_object_equal_to_original(obj):
    s = pickle.dumps(obj)

    pickled_obj = pickle.loads(s)
    return obj == pickled_obj


def test_pickling_data_structures():
    for mod in [pyds, cyds]:

        ir = mod.InternalRequest(
            request_id=999, creation_timestamp=7.89, location=(1, 3)
        )
        assert pickled_object_equal_to_original(ir)

        tr = mod.TransportationRequest(
            request_id=7,
            creation_timestamp=1.8,
            origin=(3, 7),
            destination=(2, 1),
            pickup_timewindow_min=2.13,
            pickup_timewindow_max=inf,
            delivery_timewindow_min=4.24,
            delivery_timewindow_max=inf,
        )
        assert pickled_object_equal_to_original(tr)

        stop1 = mod.Stop(
            location=ir.location,
            request=ir,
            action=mod.StopAction.internal,
            estimated_arrival_time=3.67,
            occupancy_after_servicing=0,
            time_window_min=9.12,
            time_window_max=inf,
        )
        assert pickled_object_equal_to_original(stop1)

        stop2 = mod.Stop(
            location=tr.origin,
            request=tr,
            action=mod.StopAction.pickup,
            estimated_arrival_time=2.51,
            occupancy_after_servicing=1,
            time_window_min=inf,
            time_window_max=9.13,
        )

    assert pickled_object_equal_to_original(stop2)

    if mod == cyds:
        # there's no pure python Stoplist object, so nothing to test
        stoplist = mod.Stoplist([stop1, stop2], mod.LocType.R2LOC)
        assert pickled_object_equal_to_original(stoplist)


def test_pickling_spaces(seed=42):
    for mod in (pyspaces, cyspaces):
        for space in [
            mod.Euclidean2D(velocity=1.9),
            mod.Graph.from_nx(make_nx_cycle_graph(), velocity=2.4),
        ]:
            random.seed(seed)
            x = space.random_point()
            y = space.random_point()

            s = pickle.dumps(space)
            pickled_space = pickle.loads(s)

            assert space.d(x, y) == pickled_space.d(x, y)
            assert space.t(x, y) == pickled_space.t(x, y)
