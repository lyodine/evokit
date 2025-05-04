Introduction
============

`This is the hard part: How do I write it?`

EvoKit represents evolutionary operators with classes `Individual`, `Evaluator`, `Selector`, `Variator`, and `Controller`. Components of a concrete algorithm derive from these classes.

- `Individual` represents an individual. The individual encapsulates a genome and represents additional capabilities, such as being copied and _recording information of their ancestors.

- `Evaluator` receives an individual, then assigns to it a fitness.

- `Selector` represnets both parent selection and survivor selection (replacement).

- `Variator` represents a mutator (a unary operator), a crossover operator (a binary operator), and a _I'll loook at the doc for that.

- `Controller` represents an algorithm that incorporates operators.

The user can define custom operators, or use existing ones.




Stock Selectors
~~~~~~~~~~~~~~~
The evolutionary algorithm (is that the right term?) is generic, and so is the selector. Moduels `core.controller` and `core.selector` include instances of these things.

The Genome Suite
~~~~~~~~~~~~~~~~
As the variator and the evaluator depend on the individual, the variator, the evaluator, and the individual consist of the `genome suite`. Each module in `evolvables` includes one representation and related variators and evaluators.
