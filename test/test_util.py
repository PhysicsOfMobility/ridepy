import pytest
import numpy as np
import pandas as pd
from thesimulator.util import smartVectorize


def test_smartVectorize():
    class Phony1:
        def foo(self, u, v):
            return round(u) + round(v)

    class Phony2:
        def __init__(self):
            self.n_dim = 1

        @smartVectorize
        def foo(self, u, v):
            return round(u) + round(v)

    class Phony3:
        def __init__(self):
            self.n_dim = 1

        @smartVectorize
        def foo(self, u, v):
            return round(u) + round(v)

        @foo.vectorized
        def foo(self, u, v):
            return np.round(u) + np.round(v) + 1

    phony1 = Phony1()
    phony2 = Phony2()
    phony3 = Phony3()

    ua = np.ones(100) + 0.3
    va = np.ones(100) + 0.4

    ea = np.full(100, 2, dtype="u8")

    u = ua[0]
    v = va[0]
    e = ea[0]

    ul = list(ua)
    vl = list(va)
    el = ea

    us = pd.Series(ua)
    vs = pd.Series(va)
    es = pd.Series(ea)

    for w1, w2, w3 in [
        [
            lambda u, v: phony1.foo(u, v),
            lambda u, v: phony2.foo(u, v),
            lambda u, v: phony3.foo(u, v),
        ],
        [
            lambda u, v: phony1.foo(u, v=v),
            lambda u, v: phony2.foo(u, v=v),
            lambda u, v: phony3.foo(u, v=v),
        ],
        [
            lambda u, v: phony1.foo(u=u, v=v),
            lambda u, v: phony2.foo(u=u, v=v),
            lambda u, v: phony3.foo(u=u, v=v),
        ],
    ]:

        assert w1(u, v) == e
        assert w2(u, v) == e
        assert w3(u, v) == e

        with pytest.raises(TypeError, match=r"numpy.*define __round__"):
            w1(ua, va)
        assert np.array_equal(w2(ua, va), ea)
        assert np.array_equal(w3(ua, va), ea + 1)

        with pytest.raises(TypeError, match=r"list.*define __round__"):
            w1(ul, vl)
        assert np.array_equal(w2(ul, vl), el)
        assert np.array_equal(w3(ul, vl), el + 1)

        assert np.array_equal(w1(us, vs), es)
        assert np.array_equal(w2(us, vs), es)
        assert np.array_equal(w3(us, vs), es + 1)

        x = np.zeros((100, 2))

        with pytest.raises(ValueError, match=r"2-dimension.*expected 1 dim"):
            w2(x, x)
        with pytest.raises(ValueError, match=r"2-dimension.*expected 1 dim"):
            w3(x, x)

        y = np.zeros(100)
        z = np.zeros(50)
        with pytest.raises(ValueError, match=r"shapes must match"):
            w2(y, z)
        with pytest.raises(ValueError, match=r"shapes must match"):
            w3(y, z)
