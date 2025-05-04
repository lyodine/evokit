from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple
    from typing import List
    from typing import Optional
    from typing import Self
    from typing import Any
    from collections.abc import Callable

from typing import override
from functools import wraps

from abc import ABC, abstractmethod
from types import MethodType
from typing import Generic, TypeVar

from .population import Individual, Population
import random

D = TypeVar("D", bound=Individual)


class Selector(ABC, Generic[D]):
    """Base class for all selectors.

    Derive this class to create custom selectors.

    Tutorial: :doc:`../guides/examples/selector`.
    """

    def __init__(self: Self, budget: int):
        """
        Args:
            budget: Number of individuals in the output.
        """
        self.budget = budget

    def select_to_population(self,
                             population: Population[D]) -> Population[D]:
        """Select from a population to a population.

        Invoke :meth:`select_to_many`, then shape the result into a
        :class:`.Population`.

        Args:
            population: population to select from.

        Returns:
            A new population with selected individuals.

        Effect:
            Remove all items from the original ``population`` (from
            :meth:`select_to_many`).
        """
        selected = self.select_to_many(population)
        new_population = Population[D]()
        for x in selected:
            new_population.append(x)
        return new_population

    def select_to_many(self, population: Population[D]) -> Tuple[D, ...]:
        """Context of :attr:`select`.

        Repeatedly apply select() to create a collection of solutions. Each
        application removes an item in the original population.

        A subclass may override this method to implement behaviours that
        require access to the entire selection process.

        Args:
            population: population to select from.

        Returns:
            A tuple of selected individuals.

        Effect:
            Remove all items from ``population``.
        """
        return_list: List[D] = []
        old_population: Population[D] = population

        # Determine the appropriate budget.
        # The budget cannot exceed the population size. Take the minimum of two
        #   values: (a) `self.budget` and (b) `len(population)`.
        budget_cap = min(self.budget, len(old_population))

        # Iteratively apply the selection strategy, as long as
        #   `budget_used` does not exceed `budget_cap`.
        budget_used: int = 0
        while budget_used < budget_cap:
            selected_results = self.select(old_population)
            for x in selected_results:
                population.draw(x)
            return_list.append(*selected_results)
            budget_used = budget_used + len(selected_results)
        return tuple(return_list)

    @abstractmethod
    def select(self,
               population: Population[D]) -> Tuple[D, ...]:
        """Selection strategy.

        All subclasses should override this method. The implementation should
        return a tuple of individuals. Each item in the tuple should also
        be a member of ``population``.

        Args:
            population: population to select from.

        Return:
            A tuple of selected individuals.
        """
        pass


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
    def select_to_many(self, population: Population[D]) -> Tuple[D, ...]:
        """Select every item in the population.
        """
        return tuple(x for x in population)


class SimpleSelector(Selector[D]):
    """Simple selector that select the highest-fitness individual.
    """
    @override
    def __init__(self: Self, budget: int):
        super().__init__(budget)

    def select(self,
               population: Population[D]) -> Tuple[D]:
        """Greedy selection.

        Select the item in the population with highest fitness.
        """
        population.sort(lambda x: x.fitness)
        selected_solution = population[0]
        return (selected_solution,)


class ElitistSimpleSelector(SimpleSelector[D]):
    """Elitist selector that select the highest-fitness individual.

    Example for overriding `select_to_many`. Just overriding `select`
        is not enough, because elitism requires the highest-fitness
        individual of a _population_.
    """
    @override
    def __init__(self: Self, budget: int):
        super().__init__(budget-1)
        self.best_individual: Optional[D] = None

    @override
    def select_to_many(self, population: Population[D]) -> Tuple[D, ...]:
        """Context that implements elitism.

        Preserve and update an elite. Each time the selector is used, insert
        the current elite to the results.
        """
        results: Tuple[D, ...] = super().select_to_many(population)
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
               population: Population[D]) -> Tuple[D]:
        """Tournament selection.

        Select a uniform sample, then select the best member in that sample.
        """
        # Do not select if
        #   (a) the sample is less than bracket_size, or
        #   (b) the budget is less than bracket_size
        sample: List[D]
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
                               Tuple[D, ...]]) -> Callable:

        @wraps(original_select_to_many)
        def wrapper(self: Selector[D],
                    population: Population[D],
                    *args: Any, **kwargs: Any) -> Tuple[D, ...]:
            """Context that implements elitism.
            """
            population_best: D = population.best()
            my_best: D
            
            # Monkey-patch an attribute onto the selector.
            # This attribute retains the HOF individual.
            # Current name is taken from a randomly generated SSH pubkey.
            #   Nobody else will use a name *this* absurd.
            UBER_SECRET_BEST_INDIVIDUAL_NAME = "___g1AfoA2NMh8ZZCmRJbwFcne4jS1f3Y2TRPIvBmVXQP"
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
            results: Tuple[D, ...] = \
                original_select_to_many(self, population, *args, **kwargs)

            # Append the best individual to results
            return (*results, hof_individual.copy())
        return wrapper

    setattr(sel, 'select_to_many',
            MethodType(
                wrap_function(sel.select_to_many.__func__),  # type:ignore
                sel))
    return sel
