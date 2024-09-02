Introduction
============

The class `Individual` represents an what `Variator`

This is the hard part: How do I write it?

EvoKit represents evolutionary operators with classes `Individual`, `Evaluator`, `Selector`, `Variator`, and `Controller`. Components of a concrete algorithm derive from these classes.

- `Individual` represents an individual. The individual encapsulates a genome and represents additional capabilities, such as being copied and _recording information of their ancestors.

- `Evaluator` receives an individual, then assigns to it a fitness.

- `Selector` represnets both parent selection and survivor selection (replacement).

- `Variator` represents a mutator (a unary operator), a crossover operator (a binary operator), and a _I'll loook at the doc for that.

- `Controller` represents an algorithm that incorporates operators.