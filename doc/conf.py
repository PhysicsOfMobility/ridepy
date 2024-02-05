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

sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "ridepy"
copyright = "2024, Felix Jung and Debsankha Manik"
author = "Felix Jung and Debsankha Manik"

# Aesthetics
add_function_parentheses = True


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx_toggleprompt",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx_rtd_theme",
    "sphinxcontrib.napoleon",  # for sane autodoc
    "alabaster",  # theme
    "myst_nb",  # for jupyter notebook support
    "nbsphinx_link",
]

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False  # __init__ docs merged with class doc.
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = False

# Control the order in which the members of a module are shown.
# see https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_member_order
autodoc_member_order = "bysource"
# Force the __init__ docstring to be part of the autodoc, as per
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autoclass_content
autoclass_content = "both"
default_role = "py:obj"
add_module_names = False
autodoc_typehints = "description"
autodoc_type_aliases = {
    "Event": "ridepy.events.Event",
    "RequestEvent": "ridepy.events.RequestEvent",
    "StopEvent": "ridepy.events.StopEvent",
    "SingleVehicleSolution": "ridepy.data_structures.SingleVehicleSolution",
}
autodoc_inherit_docstrings = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".ipynb": "myst-nb",
    ".myst": "myst-nb",
    ".md": "myst-nb",
}


# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

nb_custom_formats = {
    ".md": ["jupytext.reads", {"fmt": "mystnb"}],
}
