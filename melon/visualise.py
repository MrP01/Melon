"""A collection of (quality measure) visualisation helpers."""
from typing import Sequence

import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np


def priorityChart(data, title):
    """Plots a helpful priority chart.

    Adapted from https://gist.github.com/sausheong/3997c7ba8f42278866d2d15f9e63f7ad.

    Args:
        data (): data
        title (str): titles of plots
    """
    labels = ["Completed Tasks", "Important Tasks", "In Time Tasks"]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))

    colors = ["blue", "red", "green", "violet", "blueviolet", "orange", "deepskyblue", "darkgreen"]
    for d, t, c in zip(data, title, colors):
        fig = plt.figure()
        d = np.concatenate((d, [d[0]]))
        ax = fig.add_subplot(111, polar=True)
        ax.set_title(t, weight="bold", size="large")
        ax.plot(angles, d, "o-", linewidth=2, color=c)
        ax.fill(angles, d, alpha=0.25, color=c)
        ax.set_thetagrids(angles * 180 / np.pi, labels)
        ax.set_ylim(0, 1.0)
        ax.grid(True)


def plotConvergence(data: np.ndarray, labels: Sequence, filename: str | None):
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
