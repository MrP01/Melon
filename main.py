#!/usr/bin/env python
"""Main entry file for the Graphical User Interface."""
import cProfile
import logging
import pstats
import sys

from melongui.main import main

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    if "--profile" in sys.argv:
        cProfile.run("main()", sort=pstats.SortKey.CUMULATIVE)
    else:
        main()
