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

# import django
import sphinx_rtd_theme

# -- Project information -----------------------------------------------------

project = 'OpenL2M'
copyright = '2019-2025, Various'
author = 'Various'

# The full version, including alpha/beta/rc tags
release = 'v3.4 (2025-2-10)'

# --- Running on ReadTheDocs ? ---
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# -- General configuration ---------------------------------------------------

master_doc = 'index'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_rtd_theme',
#    'sphinx.ext.autodoc',
    'sphinx_design',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# this gets added to all RST files:
rst_prolog = """
.. role:: strike
    :class: strike
"""

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# https://docs.readthedocs.io/en/stable/guides/adding-custom-css.html
# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
if on_rtd:
    # need to use fontawesome from CDN
    html_css_files = [
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css',
    ]
else:
    # local server build
    html_css_files = [
        '/static/fontawesome-6.7.2/css/all.css',
    ]

# html_js_files = [
#     'js/custom.js',
# ]

# time format for the |today| output:
today_fmt = '%b %d %Y at %H:%M'

# Our source location:
# sys.path.append('/opt/openl2m/openl2m')
# sys.path.append(os.path.join(os.path.dirname(__name__), '../openl2m'))
# os.environ['DJANGO_SETTINGS_MODULE'] = 'openl2m.settings'
#import django
# django.setup()
