import pandas as pd
import numpy as np

import matplotlib.pyplot as plt


def plot_occupancy_hist(stops: pd.DataFrame, ax: plt.axes = None) -> plt.axes:
    """
    Create a occupancy histogram

    Parameters
    ----------
    stops
        stops dataframe
    ax
        axes object, optional

    Returns
    -------
    ax
        matplotlib axes

    """
    max_occ = max(stops.occupancy)
    if ax is None:
        _, ax = plt.subplots(figsize=(16, 8))

    ax.hist(
        stops["occupancy"],
        weights=stops["state_duration"],
        bins=np.r_[-0.5 : max_occ + 0.5 : 1j * (max_occ + 2)],
        rwidth=0.9,
    )
    ax.set_xticks(np.r_[0 : max_occ : 1j * (max_occ + 1)])
    ax.set_xlim((-1, max_occ + 1))
    ax.set_xlabel("occupancy")
    ax.set_ylabel("total duration at occupancy")
    ax.set_yscale("log")

    return ax
