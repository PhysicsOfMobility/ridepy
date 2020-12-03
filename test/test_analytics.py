import pytest

from thesimulator.util.spaces import Euclidean1D
from thesimulator.util.analytics import get_stops_and_requests
from thesimulator.util.analytics.plotting import plot_occupancy_hist


def test_get_stops_and_requests(initial_stoplists):
    space = Euclidean1D()
    stops, requests = get_stops_and_requests(
        events=events,
        initial_stoplists=initial_stoplists,
        transportation_requests=transportation_requests,
        space=space,
    )


def test_plot_occupancy_hist():
    ...
