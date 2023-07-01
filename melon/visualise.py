import matplotlib.pyplot as plt
import numpy as np


def chart(data, title):
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
