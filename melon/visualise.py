"""A collection of (quality measure) visualisation helpers."""

from typing import Sequence

import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np


def radarChart(values: tuple[float, float, float], title: str, filename: str | None = None):
    """Plots a helpful priority chart.

    Adapted from https://gist.github.com/sausheong/3997c7ba8f42278866d2d15f9e63f7ad.

    Args:
        data (tuple[float, float, float]): data
        title (str): titles of plots
    """
    labels = ["Completed Tasks", "Important Tasks", "In Time Tasks"]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)

    # the following three lines are only here to close the polygon
    data = values + (values[0],)
    labels.append(labels[0])
    angles = np.concatenate((angles, [angles[0]]))

    fig = plt.figure()
    axes = fig.add_subplot(1, 1, 1, polar=True)
    axes.set_title(title, weight="bold", size="large")
    axes.plot(angles, data, "o-", linewidth=2, color="blueviolet")
    axes.fill(angles, data, alpha=0.25, color="blueviolet")
    axes.set_thetagrids(angles * 180 / np.pi, labels)
    axes.set_ylim(0, 1.0)
    axes.grid(True)
    if filename is not None:
        fig.savefig(filename)  # type: ignore


def plotConvergence(data: np.ndarray, labels: Sequence, filename: str | None = None):
    """Plots convergence data to a file

    Args:
        data (np.array): data of temp, E_avg, E_var
        filename (str): path to file
    """
    fig = plt.figure()
    axes: matplotlib.axes.Axes = fig.add_subplot(3, 1, 1)
    for i in range(data.shape[0]):
        axes.plot(data[i, :, 0], label=labels[i])
    axes.set_xlabel("Iteration")
    axes.set_ylabel("Temperature $T$")
    axes.legend()
    axes: matplotlib.axes.Axes = fig.add_subplot(3, 1, 2)
    for i in range(data.shape[0]):
        axes.plot(data[i, :, 1], label=labels[i])
    axes.set_xlabel("Iteration")
    axes.set_ylabel("$E_{avg}$")
    axes.legend()
    axes: matplotlib.axes.Axes = fig.add_subplot(3, 1, 3)
    for i in range(data.shape[0]):
        axes.plot(data[i, :, 2], label=labels[i])
    axes.set_xlabel("Iteration")
    axes.set_ylabel("$E_{var}$")
    axes.legend()
    if filename is not None:
        fig.savefig(filename)  # type: ignore
