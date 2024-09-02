Installing
----------

This tutorial installs EvoKit with the |PIPMOD|_ module. Please
ensure that the module is available.

.. |PIPMOD| replace:: ``pip``
.. _PIPMOD: https://docs.python.org/3/installing/

If an error occurs during installation, update ``pip`` then try again.
If you do not wish to install EvoKit globally, please consider using
a virtual environment. An official tutorial can be found `here <https://
packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-
environments/>`_.

The build script uses the |BUILDMOD|_ module. Please install the module
or update it by running the following script:

.. |BUILDMOD| replace:: ``build``
.. _BUILDMOD: https://pypi.org/project/build/

.. code-block::

   pip install build --upgrade

Install from source
~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe/``, then run

.. code-block:: bash

   pip install .

Build a source distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe/``, then run

.. code-block:: bash

   python3 -m build --sdist

Build a built distribution (wheel)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe/``, then run

.. code-block:: bash

   python3 -m build --wheel

Build Documentation
~~~~~~~~~~~~~~~~~~~

The directory ``evoframe/docs/`` contains everything related to building documentations.

* Run ``make.bat`` to rebuild the documentation.
   
* Run ``update.bat`` to update API references in ``source/`` then rebuild the documentation.

* ``source/`` contains all configuration files, including ``conf.py``.

Trial Run
~~~~~~~~~

After installing the package, check if it is working by running

.. code-block:: bash

   python -m evokit.evolvables.binstring

or, inside a Python program or an interactive Python terminal, run

.. code-block:: python

   import evokit.evolvables.binstring as binstring
   binstring.trial_run()

The output should be a string of tuples with non-decreasing (and hopefully
increasing) values. A sample of the output follows.

   - If the values are non-decreasing, then the elitist selector
     has not failed to retain the best individual. Otherwise, the
     elitist selector is not behaving expected: either the package
     or the installation is erroneous.

   - If the values are increasing, then the variator has successfully
     improved the population. If this does not happen, try rerunning the
     program a few times.

.. code-block:: python

   (15,)
   (15,)
   (15,)
   (15,)
   (17,)
   (17,)
   (17,)
   (17,)
   (17,)
   (17,)

