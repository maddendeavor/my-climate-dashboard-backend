# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

# Add your source code directory to the Python path.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Project Name"
copyright = "2023, Maddendeavor, LLC"
author = "Christine Madden"
version = "0.0"
release = "0.0"

# Autodoc Settings
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "autoapi.extension",
]
autodoc_default_flags = ["members", "inherited-members", "undoc-members"]
autosummary_generate = True
autoapi_dirs = [os.path.normpath(os.path.join("..", "project_name/"))]
autoapi_root = "api"
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"
html_title = project
html_short_title = project


# -- Options for LaTeX output --------------------------------------------------
# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
pdf_filename = project.replace(" ", "_")
latex_documents = [
    (pdf_filename + ".tex", project, author, "manual"),
]
