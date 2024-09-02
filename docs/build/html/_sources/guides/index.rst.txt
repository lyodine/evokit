Guides
======

Base Classes
------------

Everything that form an algorithm derive from the following base classes:

Operators derive :class:`.Selector`, :class:`.Evaluator`, and :class:`.Variator`.

Algorithms derive :class:`.Algorithm`.

Representations derive :class:`.Individual`; :class:`.Population` models a population.


Getting Started
---------------

* Begin with the OneMax Problem: :doc:`examples/onemax`

* Genetic programming: :doc:`examples/gp`

* Custom selectors: :doc:`examples/selector`

* Custom algorithms: :doc:`examples/algorithm`

Advanced Tutorials
------------------

* Modify the behaviour of existing operators: :doc:`examples/interceptor`

* Collect runtime statistics with :class:`.Accountant` : :doc:`examples/accountant`.

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/accountant.ipynb
   examples/algorithm.ipynb
   examples/gp.ipynb
   examples/interceptor.ipynb
   examples/onemax.ipynb
   examples/selector.ipynb
   

   
   