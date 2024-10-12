from ..core import Accountant
from ..core import Evaluator
from ..core import Variator
from ..core import Selector
from ..core import Population
from ..core import Individual
from ..core import Algorithm

from typing import TypeVar
from typing import override


T = TypeVar("T", bound=Individual)


class SimpleLinearAlgorithm(Algorithm[T]):
    """A very simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. Individuals in the population should
    have the same type.

    The algorithm applies its operators in the following order:

        #. fire event ``GENERATION_BEGIN``
        #. **evaluate** for selection
        #. fire event ``POST_VARIATION``
        #. select for **survivors**
        #. update :attr:`population`
        #. fire event ``POST_EVALUATION``
        #. **vary** parents
        #. update :attr:`population`
        #. fire event ``POST_SELECTION``
    """
    @override
    def __init__(self,
                 population: Population[T],
                 evaluator: Evaluator[T],
                 selector: Selector[T],
                 variator: Variator[T]) -> None:
        self.population = population
        self.evaluator = evaluator
        self.selector = selector
        self.variator = variator
        self.accountants: list[Accountant] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".
        self.events: list[str] = ["GENERATION_BEGIN",
                                  "POST_VARIATION",
                                  "POST_EVALUATION",
                                  "POST_SELECTION"]

    @override
    def step(self) -> None:
        self.update("GENERATION_BEGIN")

        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.evaluator.evaluate_population(self.population)
        self.update("POST_EVALUATION")

        self.population = \
            self.selector.select_population(self.population)
        self.update("POST_SELECTION")


class LinearAlgorithm(Algorithm[T]):
    """A simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. Individuals in the population should
    have the same type.

    The algorithm applies its operators in the following order:

        #. fire event ``"GENERATION_BEGIN"``
        #. **evaluate** for parent selection
        #. fire event ``POST_PARENT_EVALUATION``
        #. select for **parents**
        #. update :attr:`population`
        #. fire event ``POST_PARENT_SELECTION``
        #. **vary** parents
        #. fire event ``POST_VARIATION``
        #. **evaluate** for survivor selection
        #. fire event ``POST_SURVIVOR_EVALUATION``
        #. select for **survivors**
        #. update :attr:`population`
        #. fire event ``POST_SURVIVOR_SELECTION``
    """
    @override
    def __init__(self,
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
        self.accountants: list[Accountant] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".
        self.events: list[str] = ["GENERATION_BEGIN",
                                  "POST_PARENT_EVALUATION",
                                  "POST_PARENT_SELECTION",
                                  "POST_VARIATION",
                                  "POST_SURVIVOR_EVALUATION",
                                  "POST_SURVIVOR_SELECTION"]

    @override
    def step(self) -> None:
        self.update("GENERATION_BEGIN")
        self.parent_evaluator.evaluate_population(self.population)
        self.update("POST_PARENT_EVALUATION")
        # Update the population after each event. This ensures that
        #   the :class:`Accountant` always has access to the most
        #   up-to-date information.
        self.population = \
            self.parent_selector.select_population(self.population)
        self.update("POST_PARENT_SELECTION")

        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.survivor_evaluator.evaluate_population(self.population)
        self.update("POST_SURVIVOR_EVALUATION")

        self.population = self.survivor_selector.select_population(
            self.population)

        self.update("POST_SURVIVOR_SELECTION")
