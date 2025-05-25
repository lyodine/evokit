|

.. image:: media/gearpath.svg
  :width: 400
  :align: center
  :alt: Image of a sequence of gears, each bigger than the last.

|

EvoKit Documentation
====================

**EvoKit** is an evolutionary computation framework written in Python. See :doc:`why` for what sets it apart.

Using EvoKit is easy! With all operators defined, you can run an evolutionary algorithm in just 7 lines! [#]_ [#]_

.. code-block:: python
   :linenos:

   ctrl: SimpleLinearAlgorithm = SimpleLinearAlgorithm(
      population=init_pop,
      variator=RandomBitMutator(0.1),
      selector=Elitist(TruncationSelector[BinaryString](POPULATION_SIZE)),
      evaluator = BitDistanceEvaluator()
   )

   for _ in range(GENERATION_COUNT):
      ctrl.step()


---------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   why
   install-and-build
   guides/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. [#] Example derived from :doc:`guides/examples/onemax`
.. [#] Technically 9 lines including parentheses and an empty line