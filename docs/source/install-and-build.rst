Installing
==========

EvoKit can be installed with |PIPMOD|_.
If an error occurs during installation, please
update ``pip`` then try again.

.. |PIPMOD| replace:: ``pip``
.. _PIPMOD: https://docs.python.org/3/installing/


If you do not wish to install EvoKit globally, consider using
a virtual environment. An official tutorial can be found `here <https://
packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-
environments/>`_.

The build script uses the |BUILDMOD|_ module.
Please install this module or update it by
running the following script:

.. |BUILDMOD| replace:: ``build``
.. _BUILDMOD: https://pypi.org/project/build/

.. code-block::

   pip install build --upgrade

Install from PiPy
-----------------

To install EvoKit directly from |EVOKIT_ON_PIPY|_, run the following command:

.. |EVOKIT_ON_PIPY| replace:: PyPi
.. _EVOKIT_ON_PIPY: https://pypi.org/project/evokit/

.. code-block:: bash

   pip install evokit

To install all optional dependencies, run the
following command:

.. code-block:: bash

   pip install evokit[full]

Install from Source
-------------------

To install EvoKit directly from source, run
the following command at the root directory:

.. code-block:: bash

   pip install .

To install all optional dependencies, run the
following command:

.. code-block:: bash

   pip install '.[full]'

Build Documentation
-------------------

The ``docs/`` directory has everything
that build the documentation:

* Run ``make.bat`` to rebuild the documentation.
   
* Run ``update.bat`` to update API references in ``source/`` then rebuild the documentation.

* ``source/`` contains all configuration files, including ``conf.py``.

Quick Start
-----------

After installing the package, you can run
a simple OneMax experiment to see if it works.

Command line:

.. code-block:: bash

   python -m evokit.evolvables.bitstring

Python code:

.. code-block:: python

   import evokit.evolvables.bitstring as bitstring
   bitstring.trial_run()

The output should be a string of tuples with
non-decreasing (and hopefully increasing) values:

   - If the values are non-decreasing, then the elitist selector
     has successfully retained the best individual.

   - If the values are increasing, then the variator has successfully
     improved the population. If this does not happen, try rerunning the
     program times.
