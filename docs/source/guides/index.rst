Guides
======

Base Classes
------------

Everything that form an algorithm derive from the following
base classes:

- Operators derive :class:`.Selector`, :class:`.Evaluator`,
  and :class:`.Variator`.

- Algorithms derive :class:`.Algorithm`.

- Representations derive :class:`.Individual`; :class:`.Population`
  models a population.

You can find an example of how these work together in
:class:`.HomogeneousAlgorithm`. The guides below give more
detailed instructions.

Getting Started
---------------

The EvoKit source code, as well as all tutorials, are *heavily* typed and
type checked with MyPy and Pylance in strict mode. Custom extensions
do not need to practice this.

* Custom representation, variator and evaluator for OneMax: :doc:`examples/onemax`

* Custom selectors: :doc:`examples/selector`

* Custom algorithms: :doc:`examples/algorithm`

.. Representations
.. ---------------

.. * Genetic programming (WIP): :doc:`examples/gp`

.. * :strike:`Linear genetic programming (RIP)`: :doc:`examples/lgp`

Advanced Tutorials
------------------

* Modify the behaviour of existing operators: :doc:`examples/interceptor`

* Collect runtime statistics with :class:`.Watcher`: :doc:`examples/watch`.

* Profile algorithm performance: :doc:`examples/profile`.

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/profile.ipynb
   examples/watch.ipynb
   examples/algorithm.ipynb
   examples/gp.ipynb
   examples/lgp.ipynb
   examples/interceptor.ipynb
   examples/onemax.ipynb
   examples/selector.ipynb


   
   