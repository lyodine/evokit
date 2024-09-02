Introduction
============

All algorithms in EvoKit derive from the following base classes:



`This is the hard part: How do I write it?`

EvoKit represents evolutionary operators with classes `Individual`, `Evaluator`, `Selector`, `Variator`, and `Controller`. Components of a concrete algorithm derive from these classes.

- `Individual` represents an individual. The individual encapsulates a genome and represents additional capabilities, such as being copied and _recording information of their ancestors.

- `Evaluator` receives an individual, then assigns to it a fitness.

- `Selector` represnets both parent selection and survivor selection (replacement).

- `Variator` represents a mutator (a unary operator), a crossover operator (a binary operator), and a _I'll loook at the doc for that.

- `Controller` represents an algorithm that incorporates operators.

The user can define custom operators, or use existing ones.


Designing novel algorithms: :doc:`examples/controller`

Getting Started
............

Genetic programming: :doc:`examples/gp`

Begin with the OneMax Problem: :doc:`examples/onemax`

Implementing custom selectors: :doc:`examples/selector`

Advanced Tutorials
..................

Modifying the behaviour of existing operators: :doc:`examples/interceptor`

Collecting runtime statistics using the :doc:`Accountant examples/accountant`


:doc:`examples/accountant`

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   examples/accountant.ipynb
   examples/controller.ipynb
   examples/gp.ipynb
   examples/interceptor.ipynb
   examples/onemax.ipynb
   examples/selector.ipynb
   

   
   