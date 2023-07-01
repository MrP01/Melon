"""Configuration file for the Sphinx documentation builder."""
import os
import sys

# used for detecting sources
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -- Project information -----------------------------------------------------
project = "Melon"
# noinspection PyShadowingBuiltins
copyright = "2022, MMSC student"
author = "An anonymous MMSC student"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "recommonmark",
]
autosummary_generate = True
# todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["build", "_templates"]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

latex_elements = {
    # "preamble": r"\usepackage{prettytex/base}",
    "printindex": ""
}
