Why EvoKit?
===========

Since its conception in 2024, EvoKit has grown to implement
a wide range of features. Please take a look at the
(:doc:`guides/index`) page for some tutorials.

EvoKit is designed to several software qualities, with
research in mind:

Simple Operators
----------------

Define only what matters and the framework will handle everything else.

The stock OneMax evaluator is written just in 3 lines. [#]_

.. literalinclude:: ../../evokit/evolvables/bitstring.py
    :language: python
    :pyobject: CountBits
    :lines: 1, 7-8

(Really) Great Interoperability
-------------------------------

Operators of the same type are interchangeable:

   * All evaluators and variators of the same representation are
     interchangeable; all selectors are interchangeable; all algorithms
     work with all compatible configurations of operators.

   * All wrappers work with everything they can wrap.
     For example, :meth:`.selectors.Elitist` can make every
     selector an elitist one and :meth:`.lineage.TrackParents`
     lets every variator preserve lineage information.

   * All operators -- variators, evaluators, and selectors
     -- can be parallelised.

   * All profilers work with all algorithms they are designed for.

See :doc:`guides/examples/profile` for how everything falls together:

    * Several stock profilers in :mod:`.watch.profile` record
      the memory usage of an algorithm.
    
    * The algorithm is a simple onemax algorithm where...
    
        * ...every operator is parallelised with 5 worker processes,
        
        * the selector is made elitist with :meth:`.selectors.Elitist` and,

        * the variator preserves several generations of parents
          with :meth:`.lineage.TrackParents`.

    * Collected statistics are plotted, against time and generation,
      with :mod:`.watch.profile.visual`.

You can swap in and out absolutely anything you want. Profit!

Completely Documented
---------------------

All public members are documented. All private members
are documented. Absolutely everything is documented.

See [:doc:`modules`] for the API documentation.

Transparent
-----------

Every single line of code is written in Python; you can see
and control everything that happens.

Furthermore, EvoKit describes exactly what it does:

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
    :lines: 3, 10-19

Portable
-----------

The `core` module has no third-party dependency and can be run on any
platform that supports Python. All dependency are optional and can be
installed later.

Reproducible
------------

All randomness in stock modules come from :mod:`random` and
can be reproduced by setting the same :meth:`random.seed`.

.. [#] ... and a few more lines for comments.