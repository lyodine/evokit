import sys
import os
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'evokit'
copyright = '2024, Yiding Li'
author = 'Yiding Li'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add path to source directory
print(f"--------------------------------------------------{os.path.abspath(os.path.join('..', '..'))}---------------")

sys.path.append(os.path.abspath(os.path.join('..', '..')))



extensions = ['nbsphinx',
              'sphinx.ext.todo',
              'sphinx.ext.viewcode',
              'sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.autosummary']

# -- Options for Typing ------------------------------------------------------

language = 'en-uk'

autoclass_content = 'class'
autosummary_generate = True

autodoc_default_options = {
    'undoc-members':     True,
    # Note: `autodoc_class_signature='separated'` causes `ClassDocumenter` to
    #   register both `__init__` and `__new__` as special members.
    # This overrides the default behaviour of not documenting private
    #   members -- even if `__new__` is marked as private, Sphinx still
    #   documents it.
    # Override the override with `'exclude-members'`, so that `__new__`
    #   is ABSOLUTELY not be documented ... until another patch breaks it.
    'exclude-members': '__new__',

}


autodoc_class_signature = 'separated'
autodoc_inherit_docstrings = False

autodoc_member_order = 'bysource'
autodoc_typehints = 'signature'
autodoc_typehints_description_target = 'all'

napoleon_use_rtype = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['styles.css',]
templates_path = ['_templates']
exclude_patterns = []

napoleon_include_special_with_doc = True

rst_prolog = """
.. role:: python(code)
  :language: python
  :class: highlight

.. role:: arg(code)

"""
