import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np


def priorityChart(data, title):
    """Plots a helpful priority chart

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


def plotConvergence(data: np.ndarray, filename: str):
    """Plots convergence data to a file

    Args:
        data (np.array): data of temp, E_avg, E_var
        filename (str): path to file
    """
    data = np.array(scheduler._log)  # type: ignore
    fig = plt.figure()
    axes: matplotlib.axes.Axes = fig.add_subplot(2, 1, 1)
    axes.plot(data[:, 1])
    axes.set_xlabel("Iteration")
    axes.set_ylabel("$E_{avg}$")
    axes: matplotlib.axes.Axes = fig.add_subplot(2, 1, 2)
    axes.plot(data[:, 2])
    axes.set_xlabel("Iteration")
    axes.set_ylabel("$E_{var}$")
    fig.savefig(filename)  # type: ignore
