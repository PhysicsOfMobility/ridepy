import pytest
import math as m
from thesimulator.util.spaces import Euclidean, Euclidean1D, Euclidean2D


def test_Euclidean1D():
    space = Euclidean1D()
    assert space.d(0, 1) == 1.0
    assert space.d(0, 0) == 0.0


def test_Euclidean2D():
    space = Euclidean2D()
    assert space.d((0, 0), (0, 1)) == 1.0
    assert space.d((0, 0), (0, 0)) == 0.0
    assert space.d((0, 0), (1, 1)) == m.sqrt(2)
