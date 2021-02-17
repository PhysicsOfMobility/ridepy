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

    assert phony1.foo(u, v) == e
    assert phony2.foo(u, v) == e
    assert phony3.foo(u, v) == e

    with pytest.raises(TypeError, match=r"numpy.*define __round__"):
        phony1.foo(ua, va)
    assert np.array_equal(phony2.foo(ua, va), ea)
    assert np.array_equal(phony3.foo(ua, va), ea + 1)

    with pytest.raises(TypeError, match=r"list.*define __round__"):
        phony1.foo(ul, vl)
    assert np.array_equal(phony2.foo(ul, vl), el)
    assert np.array_equal(phony3.foo(ul, vl), el + 1)

    assert np.array_equal(phony1.foo(us, vs), es)
    assert np.array_equal(phony2.foo(us, vs), es)
    assert np.array_equal(phony3.foo(us, vs), es + 1)

    x = np.zeros((100, 2))

    with pytest.raises(ValueError, match=r"2-dimension.*expected 1 dim"):
        phony2.foo(x, x)
    with pytest.raises(ValueError, match=r"2-dimension.*expected 1 dim"):
        phony3.foo(x, x)

    y = np.zeros(100)
    z = np.zeros(50)
    with pytest.raises(ValueError, match=r"shapes must match"):
        phony2.foo(y, z)
    with pytest.raises(ValueError, match=r"shapes must match"):
        phony3.foo(y, z)
