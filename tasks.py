"""Collection of small scripts / tasks that are usually run from the command line.
We do not use the CamelCase naming convention for methods in this file because invoke does not recognise CamelCase
function names as opposed to snake_case names.
"""
import collections
import cProfile
import pathlib
import pstats
import time

import IPython
import matplotlib.axes
import numpy as np
import requests
from invoke.context import Context
from invoke.tasks import task
from matplotlib import pyplot as plt
from traitlets.config import Config

from melon.melon import Melon
from melon.scheduler.base import generateDemoTasks, generateManyDemoTasks
from melon.scheduler.cpp import CppMCMCScheduler
from melon.scheduler.numba import NumbaMCMCScheduler
from melon.scheduler.purepython import MCMCScheduler
from melon.scheduler.rust import RustyMCMCScheduler
from melon.visualise import plotConvergence

HOME = pathlib.Path.home()
RESULTS = pathlib.Path(__file__).parent / "report" / "results"
ALL_IMPLEMENTATIONS = (MCMCScheduler, RustyMCMCScheduler, NumbaMCMCScheduler, CppMCMCScheduler)


@task()
def schedule_and_export(ctx: Context, path: str = str(HOME / "Personal" / "task-schedule.ics")):
    """Run the MCMC scheduler and export the resulting events as an ICS file.

    Args:
        ctx (invoke.Context): Invoke Execution Context
    """
    melon = Melon()
    melon.autoInit()
    scheduler = melon.scheduleAllAndExport(path, Scheduler=MCMCScheduler)
    plotConvergence(np.array(scheduler.energyLog), str(RESULTS / "convergence.pdf"))  # type: ignore


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
    """Starts a Xandikos server on port 8000.

    Args:
        ctx (Context): Invoke Execution Context
    """
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
def plot_convergence(ctx: Context, N=40):
    """Plots scheduler convergence to a file.

    Args:
        ctx (Context): Invoke Execution Context
    """
    logs = []
    tasks = generateManyDemoTasks(N)
    exponents = (-1.0, -1.5, -2.0, -3.0)
    for sweepExp in exponents:
        scheduler = MCMCScheduler(tasks)
        scheduler.sweepExponent = sweepExp
        scheduler.schedule()
        logs.append(scheduler.energyLog)
    plotConvergence(np.array(logs), [f"q = {e}" for e in exponents], str(RESULTS / "convergence.pdf"))
    ctx.run(f"xdg-open {RESULTS / 'convergence.pdf'}")


@task
def compare_runtime(ctx: Context, N=80):
    """Compares runtime of the different scheduling implementations.

    Args:
        ctx (Context): Invoke Execution Context
    """
    tasks = generateManyDemoTasks(N)
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
    return runtimes


@task()
def plot_runtime_complexity(ctx: Context):
    """Simulates with a varying number of tasks and plots runtime complexity.

    Args:
        ctx (Context): Invoke Execution Context
    """
    cumulatedRuntimes = collections.defaultdict(list)
    N_array = range(5, 80, 5)
    for N in N_array:
        runtimes = compare_runtime(ctx, N)
        for key in runtimes:
            cumulatedRuntimes[key].append(runtimes[key])

    fig = plt.figure()
    axes: matplotlib.axes.Axes = fig.add_subplot(1, 1, 1)
    for key in cumulatedRuntimes:
        axes.semilogy(N_array, cumulatedRuntimes[key], label=key)
    axes.set_xlabel("Number of tasks")
    axes.set_ylabel("Runtime")
    axes.legend()
    fig.savefig(str(RESULTS / "complexity.pdf"))  # type: ignore


@task()
def profile_scheduler(ctx: Context):
    """Profile the pure Python MCMC Scheduler.

    Args:
        ctx (Context): Invoke Execution Context
    """
    cProfile.run(
        "from melon.scheduler.purepython import MCMCScheduler;"
        "from melon.scheduler.base import generateManyDemoTasks;"
        "MCMCScheduler(generateManyDemoTasks(60)).schedule()",
        sort=pstats.SortKey.CUMULATIVE,
    )


@task()
def build_docs(ctx: Context):
    """Builds documentation using Sphinx.

    Args:
        ctx (Context): Invoke Execution Context
    """
    ctx.run("sphinx-build -M latexpdf docs/ build/docs/")


@task()
def compile(ctx: Context):
    """Assuming a full setup, compiles the low-level implementations of the scheduler algorithm in C++ and Rust.

    Args:
        ctx (Context): Invoke Execution Context
    """
    ctx.run("cargo build --release")
    print("Compiled Rust implementation.")
    with ctx.cd("build"):
        ctx.run("make -j4")
    print("Compiled C++ implementation.")
    ctx.run("cp target/release/libscheduler.so melon/scheduler/libscheduler.so")
    ctx.run("cp build/libcppscheduler.cpython-311-x86_64-linux-gnu.so melon/scheduler/libcppscheduler.so")
