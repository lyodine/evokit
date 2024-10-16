Guides
======

Base Classes
------------

Everything that form an algorithm derive from the following base classes:

- Operators derive :class:`.Selector`, :class:`.Evaluator`, and :class:`.Variator`.

- Algorithms derive :class:`.Algorithm`.

- Representations derive :class:`.Individual`; :class:`.Population` models a population.


Getting Started
---------------

* Custom representation, variator and evaluator for OneMax: :doc:`examples/onemax`

* Custom selectors: :doc:`examples/selector`

* Custom algorithms: :doc:`examples/algorithm`

Representations
---------------

* Genetic programming (WIP): :doc:`examples/gp`

* Linear genetic programming (RIP): :doc:`examples/lgp`

Advanced Tutorials
------------------

* Modify the behaviour of existing operators (WIP): :doc:`examples/interceptor`

* Collect runtime statistics with :class:`.Accountant` (WIP): :doc:`examples/accountant`.

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/accountant.ipynb
   examples/algorithm.ipynb
   examples/gp.ipynb
   examples/lgp.ipynb
   examples/interceptor.ipynb
   examples/onemax.ipynb
   examples/selector.ipynb
   

   
   