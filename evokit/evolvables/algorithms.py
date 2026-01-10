from ..watch import Watcher
from ..core import Evaluator
from ..core import Variator
from ..core import Selector
from ..core import Population
from ..core import Individual
from ..core import Algorithm

from typing import TypeVar
from typing import Any
from typing import override
from typing import Generic
from typing import Self
from abc import ABC


T = TypeVar("T", bound=Individual[Any])


class HomogeneousAlgorithm(Algorithm, ABC, Generic[T]):
    """An algorithm with one population. Exists primarily
    for typing purposes.

    Algorithms that use one homogeneous population should
    derive this class.
    """
    def __init__(self: Self) -> None:
        self.population: Population[T]


class SimpleLinearAlgorithm(HomogeneousAlgorithm[T]):
    """A very simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and
    performs one round of selection in each step.

    Each step includes the following operations:
        #. `evaluate` :attr:`population`
        #. `event`: ``POST_VARIATION``
        #. `select` from :attr:`population`
            #. `update` :attr:`population` with result
        #. `event`: ``POST_EVALUATION``
        #. `vary` :attr:`population`
            #. `update` :attr:`population` with result
        #. `event`: ``POST_SELECTION``
    """
    @override
    def __init__(self: Self,
                 population: Population[T],
                 evaluator: Evaluator[T],
                 selector: Selector[T],
                 variator: Variator[T]) -> None:
        self.population = population
        self.evaluator = evaluator
        self.selector = selector
        self.variator = variator
        self.watchers: list[Watcher[SimpleLinearAlgorithm[T], Any]] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".

    events = ["POST_VARIATION",
              "POST_EVALUATION",
              "POST_SELECTION"]

    @override
    def step(self: Self) -> None:
        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.evaluator.evaluate_population(self.population)
        self.update("POST_EVALUATION")

        self.population = self.selector.select_population(self.population)
        self.update("POST_SELECTION")


class LinearAlgorithm(HomogeneousAlgorithm[T]):
    """A general evolutionary algorithm [SIMPLE_GA]_.

    An evolutionary algorithm that maintains one population. Each
    step includes two rounds of selection.

    Each step includes the following operations:
        #. evaluate :attr:`population`
        #. `event`: ``POST_PARENT_EVALUATION``
        #. select parents from :attr:`population`
            #. `update` :attr:`population` with result
        #. `event`: ``POST_PARENT_SELECTION``
        #. vary :attr:`population`
        #. `event`: ``POST_VARIATION``
        #. evaluate :attr:`population`
        #. `event`: ``POST_OFFSPRING_EVALUATION``
        #. select survivors from :attr:`population`
            #. `update` :attr:`population` with result
        #. `event`: ``POST_OFFSPRING_SELECTION``

    .. [SIMPLE_GA] Introduction to Evolutionary Computing [2nd ed.],
       A. E. Eiben and J. E. Smith (2015), Fig 3.1
    """
    @override
    def __init__(self: Self,
                 population: Population[T],
                 parent_evaluator: Evaluator[T],
                 parent_selector: Selector[T],
                 variator: Variator[T],
                 survivor_evaluator: Evaluator[T],
                 survivor_selector: Selector[T]) -> None:
        # _Introduction to Evolutionary Computing_ calls
        #   selectors "survivor selection" and the outcome
        #   "offspring". These terms are taken from that book.
        self.population = population
        self.parent_evaluator = parent_evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.survivor_evaluator = survivor_evaluator
        self.survivor_selector = survivor_selector
        self.watchers: list[Watcher[LinearAlgorithm[T], Any]] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".

    events = ["POST_PARENT_EVALUATION",
              "POST_PARENT_SELECTION",
              "POST_VARIATION",
              "POST_OFFSPRING_EVALUATION",
              "POST_OFFSPRING_SELECTION"]

    @override
    def step(self) -> None:
        self.parent_evaluator.evaluate_population(self.population)
        self.update("POST_PARENT_EVALUATION")
        # Update the population after each event. This ensures that
        #   the :class:`Watcher` always has access to the most
        #   up-to-date information.
        self.population = \
            self.parent_selector.select_population(self.population)
        self.update("POST_PARENT_SELECTION")

        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.survivor_evaluator.evaluate_population(self.population)
        self.update("POST_OFFSPRING_EVALUATION")

        self.population = self.survivor_selector.select_population(
            self.population)

        self.update("POST_OFFSPRING_SELECTION")


class CanonicalGeneticAlgorithm(HomogeneousAlgorithm[T]):
    """The canonical genetic algorithm [CANON_GA]_.

    An evolutionary algorithm that consecutively apply
    two variators. In Holland's foundational algorithm,
    these are crossover followed by mutation.

    Each step includes the following operations:
        #. vary :attr:`population` with :attr:`variator1`
        #. `event`: ``POST_VARIATION_1``
        #. vary :attr:`population` with :attr:`variator2`
        #. `event`: ``POST_VARIATION_2``
        #. evaluate :attr:`population`
        #. `event`: ``POST_EVALUATION``
        #. select survivors from :attr:`population`
            #. `update` :attr:`population` with result
        #. `event`: ``POST_SELECTION``

    .. [CANON_GA] Adaptation in Natural and Artificial Systems,
       Holland (1975)
    """
    @override
    def __init__(self: Self,
                 population: Population[T],
                 evaluator: Evaluator[T],
                 selector: Selector[T],
                 variator1: Variator[T],
                 variator2: Variator[T]) -> None:
        self.population = population
        self.evaluator = evaluator
        self.selector = selector
        self.variator1 = variator1
        self.variator2 = variator2
        self.watchers: list[
            Watcher[CanonicalGeneticAlgorithm[T], Any]] = []

    events = ["POST_VARIATION_1", "POST_VARIATION_2",
              "POST_EVALUATION", "POST_SELECTION"]

    @override
    def step(self: Self) -> None:
        self.population = self.variator1.vary_population(self.population)
        self.update("POST_VARIATION_1")

        self.population = self.variator2.vary_population(self.population)
        self.update("POST_VARIATION_2")

        self.evaluator.evaluate_population(self.population)
        self.update("POST_EVALUATION")

        self.population = self.selector.select_population(self.population)
        self.update("POST_SELECTION")
