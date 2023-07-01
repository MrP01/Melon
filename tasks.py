"""Collection of small scripts / tasks that are usually run from the command line.
We do not use the CamelCase naming convention for methods in this file because invoke does not recognise CamelCase
function names as opposed to snake_case names.
"""
import pathlib
import time

import IPython
import numpy as np
import requests
from invoke.context import Context
from invoke.tasks import task
from traitlets.config import Config

from melon.melon import Melon
from melon.scheduler.base import generateDemoTasks, generateManyDemoTasks
from melon.scheduler.cpp import CppMCMCScheduler
from melon.scheduler.numba import NumbaMCMCScheduler
from melon.scheduler.purepython import MCMCScheduler
from melon.scheduler.rust import RustyMCMCScheduler
from melon.visualise import plotConvergence

ALL_IMPLEMENTATIONS = (MCMCScheduler, RustyMCMCScheduler, NumbaMCMCScheduler, CppMCMCScheduler)

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
    plotConvergence(np.array(scheduler._log), str(RESULTS / "convergence.pdf"))  # type: ignore


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


@task()
def plot_convergence(ctx: Context):
    """Plots scheduler convergence to a file."""
    scheduler = MCMCScheduler(generateDemoTasks())
    scheduler.schedule()
    plotConvergence(np.array(scheduler._log), str(RESULTS / "convergence.pdf"))  # type: ignore


@task
def compare_runtime(ctx: Context):
    """Compares runtime of the different scheduling implementations."""
    tasks = generateManyDemoTasks(80)
    start = time.monotonic()
    NumbaMCMCScheduler(generateDemoTasks()).schedule()  # warm-up / pre-compile Numba
    print("Numba Compilation time:", time.monotonic() - start)
    runtimes = {}
    for Scheduler in ALL_IMPLEMENTATIONS:
        print(Scheduler)
        scheduler = Scheduler(tasks)
        start = time.monotonic()
        scheduler.schedule()
        runtimes[Scheduler.__name__] = time.monotonic() - start
    for key, value in sorted(runtimes.items(), key=lambda item: item[1]):
        print(f"{key:40} took {value:.4f} seconds")
