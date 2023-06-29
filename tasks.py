"""Collection of small scripts / tasks that are usually run from the command line.
We do not use the CamelCase naming convention for methods in this file because invoke does not recognise CamelCase
function names as opposed to snake_case names.
"""
import pathlib

from invoke.context import Context
from invoke.tasks import task

from melon.melon import Melon

HOME = pathlib.Path.home()


@task()
def schedule_and_export(ctx: Context, path: str = str(HOME / "Personal" / "task-schedule.ics")):
    """Run the MCMC scheduler and export the resulting events as an ICS file.

    Args:
        ctx (invoke.Context): Invoke Execution Context
    """
    melon = Melon()
    melon.init()
    melon.scheduleAllAndExport(path)
