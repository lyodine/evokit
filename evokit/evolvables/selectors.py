from ..core import Selector
from ..core import Population
from ..core import Individual

import random

from typing import Self

from typing import Any
from typing import TypeVar
from typing import Sequence
from typing import Callable
from typing import override
from types import MethodType
from functools import wraps

from operator import attrgetter

D = TypeVar("D", bound=Individual[Any])


class NullSelector(Selector[D]):
    """Selector that does nothing.
    """
    @override
    def __init__(self: Self):
        pass

    @override
    def select_population(self: Self,
                          from_population: Population[D]) -> Population[D]:
        """Return all items in :arg:`from_population` in  new population.
        """
        return Population(*from_population)


class TruncationSelector(Selector[D]):
    """Simple selector that select individuals with highest fitness.
    """
    @override
    def __init__(self: Self, budget: int):
        super().__init__(budget)

    @override
    def select_population(self: Self,
                          from_population: Population[D]) -> Population[D]:
        return Population[D](*sorted(list(from_population),
                                     key=attrgetter("fitness"))[-self.budget:])


class TournamentSelector(Selector[D]):
    """Tournament selector:

    #. From the population, select uniform sample of size :arg:`bracket_size`.

    #. Iterate through the sample, stop when a selection is made.
       At index ``i``, select that item with probability :math:`p * (1- p)^i`.
       If no selection is made when reaching the end of the sample, select
       the last item.

    #. Repeat until :arg:`budget` items are selected.
    """
    def __init__(self: Self, budget: int, bracket_size: int = 2,
                 p: float = 1):
        super().__init__(budget)
        self.bracket_size: int = bracket_size
        self.p: float = min(2, max(p, 0))

    @override
    def select(self, from_pool: Sequence[D]) -> tuple[D]:
        """Tournament selection.

        Select a uniform sample, then select the best member in that sample.
        """
        sample: list[D]

        budget_cap: int = min(len(from_pool), self.budget)

        # Ensure: the size of a sample must not exceed the output arity.
        if budget_cap < self.bracket_size:
            sample = list(from_pool)
        else:
            # For some reason `random.sample` returns a list.
            sample = random.sample(tuple(from_pool), self.bracket_size)

        sample.sort(key=lambda x: x.fitness, reverse=True)

        # Iterate items, select each with probability p * (1 - p)**i.
        for i in range(len(sample)):
            if random.random() < self.p * (1 - self.p)**i:
                return (sample[i],)

        # If nothing is selected in the end, select the last element
        return (sample[-1],)


def Elitist(sel: Selector[D]) -> Selector[D]:
    """Decorator that adds elitism to a selector.

    Retain and update the highest-fitness individual encountered so far.
    Each time the selector is called, append that individual to the end
    of the output population.

    Modify `select_population` of `sel` to use elitism. If `sel` already
    overrides `select_population`, that implementation is destroyed.

    Args:
        sel: A selector

    Return:
        A selector
    """

    def wrap_function(original_select_population:
                      Callable[[Selector[D], Population[D]],
                               Population[D]])\
            -> Callable[[Selector[D], Population[D]], Population[D]]:

        @wraps(original_select_population)
        def wrapper(self: Selector[D],
                    population: Population[D],
                    *args: Any, **kwargs: Any) -> Population[D]:
            """Context that implements elitism.
            """
            population_best: D = population.best()
            my_best: D

            # Monkey-patch an attribute onto the selector.
            # This attribute retains the HOF individual.
            # Current name is taken from a randomly generated SSH pubkey.
            #   Nobody else will use a name *this* absurd.
            BEST_INDIVIDUAL_ATTR_NAME =\
                "___g1AfoA2NMh8ZZCmRJbweeee4jS1f3Y2TRPIvBmVXQP"
            if not hasattr(self, BEST_INDIVIDUAL_ATTR_NAME):
                setattr(self, BEST_INDIVIDUAL_ATTR_NAME,
                        population_best.copy())

            hof_individual: D
            my_best = getattr(self, BEST_INDIVIDUAL_ATTR_NAME)

            if my_best.fitness > population_best.fitness:
                hof_individual = my_best
            else:
                hof_individual = population_best
                setattr(self, BEST_INDIVIDUAL_ATTR_NAME,
                        population_best.copy())

            # Acquire results of the original selector
            results: Population[D] = \
                original_select_population(self, population, *args, **kwargs)

            # Append the best individual to results
            return Population(*results, hof_individual.copy())
        return wrapper

    setattr(sel, 'select_population',
            MethodType(
                wrap_function(sel.select_population.__func__),  # type:ignore
                sel))
    return sel
