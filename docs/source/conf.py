# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


with open('../../VERSION') as version_file:
    version = version_file.read().strip()

project = 'AIDA-TLU'
copyright = '2023, SiLab, Institute of Physics, University of Bonn'
author = 'Rasmus Partzsch'
release = version

import sys
import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../aidatlu'))
sys.path.insert(0, os.path.abspath('../aidatlu/hardware'))
sys.path.insert(0, os.path.abspath('../aidatlu/main'))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx_mdinclude',
    'sphinx.ext.viewcode',
    ]

autosectionlabel_prefix_document = True

templates_path = ['_templates']
exclude_patterns = []


source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

autodoc_mock_imports = ["hardware", "DutLogic", "main", "uhal"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

html_theme_options = {
    #[...]
    # "show_toc_level": 2,
    # "show_nav_level": 3,
    "primary_sidebar_end": ["indices.html", "sidebar-ethical-ads.html"],
    "secondary_sidebar_items": [],
    #[...]
}

html_sidebars = {
    '*': ["page-toc", "edit-this-page", "sourcelink"]
}
