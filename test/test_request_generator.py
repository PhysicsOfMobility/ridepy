import itertools as it

from ridepy.util.request_generators import RandomRequestGenerator
from ridepy.util.spaces import Euclidean1D, Euclidean2D, Graph
from ridepy.extras.spaces import make_nx_grid


def test_random_request_generator():
    rg = RandomRequestGenerator(space=Euclidean2D())
    reqs = list(it.islice(rg, 10))
    assert len(reqs) == 10
    assert all(
        reqs[i + 1].creation_timestamp > reqs[i].creation_timestamp for i in range(9)
    )
    for r in reqs:
        assert r.request_id is not None
        assert len(r.origin) == 2
        assert len(r.destination) == 2
        assert 0 <= r.origin[0] <= 1
        assert 0 <= r.origin[1] <= 1
        assert 0 <= r.destination[0] <= 1
        assert 0 <= r.destination[1] <= 1


def test_random_request_generator_no_trivial():
    for space in [Graph.from_nx(make_nx_grid()), Euclidean1D(), Euclidean2D()]:
        rg = RandomRequestGenerator(space=space)
        assert all(req.origin != req.destination for req in it.islice(rg, 10000))
