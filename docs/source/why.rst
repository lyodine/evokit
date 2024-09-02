Why EvoKit?
===========

Operators are Easy to Make
-----------------------------

When extending a framework, you can just define what matters. The framework takes care of the rest.

Define the OneMax evaluator in 3 lines!

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

**All** public members are documented (see [:doc:`modules`]).

**All** private member (except for well-known dunders) are thoroughly described. You can find examples like this in the source code:

.. literalinclude:: ../../evokit/evolvables/gp.py
    :language: python
    :pyobject: _get_arity
    :lines: 1-12

Well Described
--------------

**EvoKit** describes exactly what it does.

* All methods (public or private) have type hints:

.. literalinclude:: ../../evokit/core/controller.py
    :language: python
    :pyobject: SimpleLinearController.__init__
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

.. literalinclude:: ../../evokit/core/controller.py
    :language: python
    :pyobject: Controller.step
    :lines: 2, 3, 20-24

Transparent
-----------

Core modules (in :mod:`.core`) do not depend on any external module.

All randomness come from :mod:`.random` and can be reproduced by setting the right :meth:`.random.seed`.
