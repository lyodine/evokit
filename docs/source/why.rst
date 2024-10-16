Why EvoKit?
===========

Operators are Easy to Make
-----------------------------

Define only what matters, let the framework automate wht it can.

The stock OneMax evaluator is written just in 3 lines! [#]_

.. literalinclude:: ../../evokit/evolvables/binstring.py
    :language: python
    :pyobject: CountBits
    :lines: 1, 7-8

Operators are Interchangeable
-----------------------------

Operators of the same type are interchangeable. That is:

   * **All** evaluators and variators of the same representation are interchangeable.

   * **All** selectors are interchangeable.

   * **All** algorithms work with **all** configurations of compatible operators.

Completely Documented
---------------------

**All** public members are documented (see [:doc:`modules`] for the API documentation).

**All** private members (except for well-known dunders) are documented. You can find examples like this in the source code:

.. literalinclude:: ../../evokit/evolvables/gp.py
    :language: python
    :pyobject: _get_arity
    :lines: 1-12

Well Described
--------------

**EvoKit** describes exactly what it does.

* All methods (public or private) have type hints:

.. literalinclude:: ../../evokit/evolvables/algorithms.py
    :language: python
    :pyobject: SimpleLinearAlgorithm.__init__
    :lines: 2-6

* All return values are explained:

.. literalinclude:: ../../evokit/core/population.py
    :language: python
    :pyobject: Individual.has_fitness

* All effects are documented:

.. literalinclude:: ../../evokit/core/population.py
    :language: python
    :pyobject: Individual.reset_fitness

* All managed attributes are explained:

.. literalinclude:: ../../evokit/core/algorithm.py
    :language: python
    :pyobject: Algorithm.step
    :lines: 2, 3, 20-24

Transparent
-----------

Core modules (in :mod:`.core`) do not depend on any external module.

Reproducible
------------

All randomness in existing modules come from :mod:`random` and
can be reproduced by setting the same :meth:`random.seed`.

.. [#] ... and a few more lines for comments.