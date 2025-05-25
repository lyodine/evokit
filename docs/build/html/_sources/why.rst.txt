Why EvoKit?
===========

Operators are Interchangeable
-----------------------------

Operators of the same type are interchangeable. That is:

   * **All** evaluators of the same representation are interchangeable.

   * **All** variators of the same representation are interchangeable.

   * **All** selectors are interchangeable.

   * **All** algorithms work with **all** combinations of operators, as long as the operators are compatible.

Completely Documented
---------------------

Every single public member is documented at [:doc:`modules`]. All private members are richly commented.

All private members, except for well-known dunders, are also documented:

.. literalinclude:: ../../evokit/evolvables/gp.py
    :language: python
    :pyobject: _get_arity
    :lines: 1-12

Completely Typed
----------------

Every single method is type hinted; every return value is explained; every effect is mentioned.

.. literalinclude:: ../../evokit/core/controller.py
    :language: python
    :pyobject: SimpleLinearController.__init__
    :lines: 2-6




Transparent
-----------

Core modules (:mod:`core`) do not depend on external modules.

All randomness come from :mod:`random` and can be changed by setting :meth:`random.seed`.
