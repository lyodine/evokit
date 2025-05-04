Installing
----------

Install from source
~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe``, then run

.. code-block:: bash

   pip install .

Installing and Building
~~~~~~~~~~~~~~~~~~~~~~~

EvoKit is built with `build`_. Please ensure that your ``build`` is up to date. Run

.. _build: https://pypi.org/project/build/

.. code-block::

   pip install build --upgrade

Build a source distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe``, then run

.. code-block:: bash

   python3 -m build --sdist

Build a built distribution (wheel)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate to ``evoframe``, then run

.. code-block:: bash

   python3 -m build --wheel

Build Documentation
~~~~~~~~~~~~~~~~~~~

The directory ``evoframe/docs`` contains everything related to building documentations.

   * ``make.bat`` rebuilds the documentation.
   
   * ``source/`` contains the configuration files. 

   * ``update.bat`` updates ``source/`` to capture the current source code, then runs ``make.bat``