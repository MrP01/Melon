"""Collection of small scripts / tasks that are usually run from the command line.
We do not use the CamelCase naming convention for methods in this file because invoke does not recognise CamelCase
function names as opposed to snake_case names.
"""
import pathlib
import time

import IPython
import matplotlib.axes
import matplotlib.figure
import numpy as np
import requests
from invoke.context import Context
from invoke.tasks import task
from matplotlib import pyplot as plt
from traitlets.config import Config

from melon.melon import Melon
from melon.scheduler.purepython import MCMCScheduler

HOME = pathlib.Path.home()
RESULTS = pathlib.Path(__file__).parent / "report" / "results"


@task()
def schedule_and_export(ctx: Context, path: str = str(HOME / "Personal" / "task-schedule.ics")):
    """Run the MCMC scheduler and export the resulting events as an ICS file.

    Args:
        ctx (invoke.Context): Invoke Execution Context
    """
    melon = Melon()
    melon.autoInit()
    scheduler = melon.scheduleAllAndExport(path, Scheduler=MCMCScheduler)

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
    fig.savefig(str(RESULTS / "convergence.pdf"))  # type: ignore
    plt.show()


@task()
def ipython_shell(ctx: Context):
    """Starts an IPython shell with Melon initialised.

    Args:
        ctx (Context): Invoke Execution Context
    """
    config = Config()
    config.InteractiveShellApp.exec_lines = [  # type: ignore
        "from melon.melon import Melon",
        "melon = Melon()",
        "melon.init()",
    ]
    IPython.start_ipython([], config=config)


@task()
def start_mock_server(ctx: Context):
    """Starts a Xandikos server on port 8000."""
    ctx.run("mkdir -p /tmp/xandikosdata")
    ctx.sudo(
        "docker run -v /tmp/xandikosdata:/data -p 8000:8000 --detach ghcr.io/jelmer/xandikos "
        "--route-prefix=/dav --current-user-principal=/user",
        warn=True,
    )
    time.sleep(1.0)
    response = requests.get("http://localhost:8000/")
    print("Server reachable:", response.ok)
    melon = Melon(url="http://localhost:8000/dav/user/calendars/")
    melon.fetch()
    assert melon.principal is not None
    if "pytest" not in melon.calendars:
        melon.principal.make_calendar("pytest")
        print("Created calendar `pytest`.")
    else:
        print("`pytest` calendar already exists.")
    melon.store()
