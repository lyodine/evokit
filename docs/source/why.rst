Why EvoKit?
===========

Since its conception in 2024, EvoKit has grown to implement
a wide range of features. Please take a look at
:doc:`guides/index` for some tutorials.

EvoKit is designed to several software qualities, with
researchers in mind:

Simple Operators
----------------

Define only what matters and the framework will
handle the rest.

The stock OneMax evaluator, for example, is written just
in 3 lines: [#]_

.. literalinclude:: ../../evokit/evolvables/bitstring.py
    :language: python
    :pyobject: CountBits
    :lines: 1, 7-8

(Really) Great Interoperability
-------------------------------

Everything are interoperable and most
things are interchangeable:

   * All evaluators and variators of the same representation are
     interchangeable; all selectors are interchangeable; all algorithms
     work with all compatible configurations of operators.

   * All wrappers of the same operator type are interchangeable.
     For example, :meth:`.selectors.Elitist` works with every
     selector and :meth:`.lineage.TrackParents` works
     with every variator.

   * All operators -- variators, evaluators, and selectors
     -- can be parallelised.

   * All profilers work with all algorithms of the right type.

See :doc:`guides/examples/profile` for how these pieces
falls together. Here:

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

See :doc:`modules` for the API documentation.

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

EvoKit has no mandatory dependency. All dependencies are
optional and can be installed later, only when you need them.

Reproducible
------------

All randomness in stock modules come from :mod:`random` and
can be reproduced by setting the same :meth:`random.seed`.

.. [#] ... and a few more lines for comments.