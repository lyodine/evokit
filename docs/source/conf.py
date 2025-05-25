# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Evoframe'
copyright = '2024, Yiding Li'
author = 'Yiding Li'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add path to source directory
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', '..', 'src')))

extensions = ['sphinx.ext.todo',
              'sphinx.ext.viewcode',
              'sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.autosummary']

# -- Options for Typing ------------------------------------------------------

language = 'en-uk'

autoclass_content = 'class'
autosummary_generate = True

autodoc_default_options = {
    'members':           True,
    'undoc-members':     True,
}
autodoc_class_signature='separated'
autodoc_inherit_docstrings=True
autodoc_member_order = 'bysource'
autodoc_typehints='signature'
autodoc_typehints_description_target = 'all'

napoleon_use_rtype = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_css_files = ['styles.css',]
html_static_path = ['_static']
templates_path = ['_templates']
exclude_patterns = []
