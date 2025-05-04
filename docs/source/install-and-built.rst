Installing
----------

Install from source
~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe``, then run

.. code-block:: bash

   pip install .

Installing and Building
~~~~~~~~~~~~~~~~~~~~~~~

EvoKit is built with `build`_. To ensure that ``build`` is up to date, run

.. _build: https://pypi.org/project/build/

.. code-block::

   pip install build --upgrade

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
