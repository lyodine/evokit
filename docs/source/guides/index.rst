Guides
======

Base Classes
------------

Everything that form an algorithm derive from the following base classes:

All algorithms in EvoKit derive from the following base classes: :class:`.Selector`, :class:`.Evaluator`, and :class:`.Variator`.

The :class:`.Controller` represents an algorithm.

The :class:`.Individual` represents an individual, many individuals form a :class:`.Population`




Getting Started
---------------

   * Begin with the OneMax Problem: :doc:`examples/onemax`

   * Genetic programming: :doc:`examples/gp`

   * Custom selectors: :doc:`examples/selector`

   * Custom algorithms: :doc:`examples/controller`

Advanced Tutorials
------------------

   * Modifying the behaviour of existing operators: :doc:`examples/interceptor`

   * :doc:`examples/accountant` Collecting runtime statistics using the.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   examples/accountant.ipynb
   examples/controller.ipynb
   examples/gp.ipynb
   examples/interceptor.ipynb
   examples/onemax.ipynb
   examples/selector.ipynb
   

   
   