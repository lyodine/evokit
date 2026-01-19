Guides
======

Here are some tutorials to get started:

Getting Started
---------------

* Custom representation, variator and evaluator for
  OneMax: :doc:`examples/onemax`.

* Custom selectors: :doc:`examples/selector`.

* Custom algorithms: :doc:`examples/algorithm`.

* Collect runtime statistics with :class:`.Watcher`:
  :doc:`examples/watch`.

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/onemax.ipynb
   examples/selector.ipynb
   examples/algorithm.ipynb
   examples/watch.ipynb
   

Representations
---------------

* Genetic programming: :doc:`examples/gp`

.. * :strike:`Linear genetic programming (RIP)`: :doc:`examples/lgp`

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/gp.ipynb

Advanced Tutorials
------------------

* Modify the behaviour of existing operators:
  :doc:`examples/interceptor`

* Profile algorithm performance:
  :doc:`examples/profile`.

.. toctree::
   :maxdepth: 2
   :caption: What:
   :hidden:

   examples/profile.ipynb
   examples/lgp.ipynb
   examples/interceptor.ipynb

Learning from Documentation
---------------------------

The source code of EvoKit is heavily documented
and typed. Because I too like to learn from
documentation, I want to make it as easy as
possible for you.

EvoKit's building blocks derive the following
classes:

- Operators derive :class:`.Selector`, :class:`.Evaluator`,
  and :class:`.Variator`.

- Algorithms derive :class:`.Algorithm`.

- Representations derive :class:`.Individual`; :class:`.Population`
  models a population.

You can find an example of how these work together
in :class:`.HomogeneousAlgorithm`. The guides below give more
detailed instructions.




   
   