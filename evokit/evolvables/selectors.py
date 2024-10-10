from ..core import Selector
from ..core import Population
from ..core import Individual

import random

from typing import Self
from typing import Any
from typing import TypeVar
from typing import Optional
from typing import Callable
from typing import override
from types import MethodType
from functools import wraps


D = TypeVar("D", bound=Individual)


class NullSelector(Selector[D]):
    """Selector that does nothing.
    """
    @override
    def __init__(self: Self):
        pass

    @override
    def select(self: Self, *_: Any, **__: Any) -> Any:
        pass

    @override
    def select_to_many(self, population: Population[D]) -> tuple[D, ...]:
        """Select every item in the population.
        """
        return tuple(x for x in population)


class TruncationSelector(Selector[D]):
    """Simple selector that select the highest-fitness individual.
    """
    @override
    def __init__(self: Self, budget: int):
        super().__init__(budget)

    def select(self,
               population: Population[D]) -> tuple[D]:
        """Greedy selection.

        Select the item in the population with highest fitness.
        """
        population.sort(lambda x: x.fitness)
        selected_solution = population[0]
        return (selected_solution,)


class ElitistTruncationSelector(TruncationSelector[D]):
    """Elitist selector that select the highest-fitness individual.

    Example for overriding `select_to_many`. Just overriding `select`
        is not enough, because elitism requires the highest-fitness
        individual of a _population_.
    """
    @override
    def __init__(self: Self, budget: int):
        super().__init__(budget - 1)
        self.best_individual: Optional[D] = None

    @override
    def select_to_many(self, population: Population[D]) -> tuple[D, ...]:
        """Context that implements elitism.

        Preserve and update an elite. Each time the selector is used, insert
        the current elite to the results.
        """
        results: tuple[D, ...] = super().select_to_many(population)
        best_individual: Optional[D] = self.best_individual
        if best_individual is None:
            best_individual = results[0]
        for x in results:
            if x.fitness < best_individual.fitness:
                best_individual = x
        self.best_individual = best_individual

        return (*results, self.best_individual)


class TournamentSelector(Selector[D]):
    """Tournament selector.
    """
    def __init__(self: Self, budget: int, bracket_size: int = 2,
                 probability: float = 1):
        super().__init__(budget)
        self.bracket_size: int = bracket_size
        self.probability: float = min(2, max(probability, 0))

    @override
    def select(self,
               population: Population[D]) -> tuple[D]:
        """Tournament selection.

        Select a uniform sample, then select the best member in that sample.
        """
        # Do not select if
        #   (a) the sample is less than bracket_size, or
        #   (b) the budget is less than bracket_size
        sample: list[D]
        if min(len(population), self.budget) < self.bracket_size:
            sample = list(population)
        else:
            sample = random.sample(tuple(population), self.bracket_size)
        sample.sort(key=lambda x: x.fitness, reverse=True)

        # If nothing is selected stochastically, select the last element
        selected_solution: D = sample[-1]

        # Select the ith element with probability p * (1-p)**i
        probability = self.probability
        for i in range(len(sample)):
            if random.random() < probability * (1 - probability)**i:
                selected_solution = sample[i]
                break

        return (selected_solution,)


def Elitist(sel: Selector[D]) -> Selector:
    """Decorator that adds elitism to a selector.

    Retain and update the highest-fitness individual encountered so far.
    Each time the selector is called, append that individual to the end
    of the output population.

    Modify `select_to_many` of `sel` to use elitism. If `sel` already
        overrides `select_to_many`, that implementation is destroyed.

    Args:
        sel: A selector

    Return:
        A selector
    """

    def wrap_function(original_select_to_many:
                      Callable[[Selector[D], Population[D]],
                               tuple[D, ...]]) -> Callable:

        @wraps(original_select_to_many)
        def wrapper(self: Selector[D],
                    population: Population[D],
                    *args: Any, **kwargs: Any) -> tuple[D, ...]:
            """Context that implements elitism.
            """
            population_best: D = population.best()
            my_best: D

            # Monkey-patch an attribute onto the selector.
            # This attribute retains the HOF individual.
            # Current name is taken from a randomly generated SSH pubkey.
            #   Nobody else will use a name *this* absurd.
            UBER_SECRET_BEST_INDIVIDUAL_NAME =\
                "___g1AfoA2NMh8ZZCmRJbwFcne4jS1f3Y2TRPIvBmVXQP"
            if not hasattr(self, UBER_SECRET_BEST_INDIVIDUAL_NAME):
                setattr(self, UBER_SECRET_BEST_INDIVIDUAL_NAME, population_best.copy())

            hof_individual: D
            my_best = getattr(self, UBER_SECRET_BEST_INDIVIDUAL_NAME)

            if my_best.fitness > population_best.fitness:
                hof_individual = my_best
            else:
                hof_individual = population_best
                setattr(self, UBER_SECRET_BEST_INDIVIDUAL_NAME, population_best.copy())

            # Acquire results of the original selector
            results: tuple[D, ...] = \
                original_select_to_many(self, population, *args, **kwargs)

            # Append the best individual to results
            return (*results, hof_individual.copy())
        return wrapper

    setattr(sel, 'select_to_many',
            MethodType(
                wrap_function(sel.select_to_many.__func__),  # type:ignore
                sel))
    return sel
