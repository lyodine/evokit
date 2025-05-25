from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple
    from typing import List
    from typing import Optional
    from typing import Self

from abc import ABC, abstractmethod
from types import MethodType
from typing import Generic, TypeVar

from .population import Individual, Population
import random

T = TypeVar("T", bound=Individual)


class Selector(ABC, Generic[T]):
    """Base class for all selectors.

    Derive this class to create custom selectors.
    """

    def __init__(self: Self, budget: int):
        """
        Args:
            budget: Number of individuals in the output.
        """
        self.budget = budget

    def select_to_population(self,
                             population: Population[T]) -> Population[T]:
        """As an offspring selector, select from a population to a population.

        Args:
            population: population to select from.
        """
        selected = self.select_to_many(population)
        new_population = Population[T]()
        for x in selected:
            new_population.append(x)

        return new_population

    def select_to_many(self, population: Population[T]) -> Tuple[T, ...]:
        """Context for the selection strategy.

        Repeatedly apply select() to create a collection of solutions.
        A subclass may override this method to implement behaviours that
            require access to the entire selection process.

        Args:
            population: population to select from.
        """

        return_list: List[T] = []
        old_population: Population[T] = population

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
               population: Population[T]) -> Tuple[T, ...]:
        """Selection strategy of the selector.

        All subclasses should override this method. The implementation should
            return a tuple of individuals. Each item in the tuple should also
            be a member of `population`.

        Args:
            population: population to select from.
        """
        pass


class NullSelector(Selector[T]):
    """Selector that does nothing.

    """
    def select_to_many(self, population: Population[T]) -> Tuple[T, ...]:
        """Select every item in the population.
        """
        return tuple(x for x in population)


class SimpleSelector(Selector[T]):
    """Simple selector that select the highest-fitness individual.

    Example for overriding `select`.
    """
    def __init__(self: Self, budget: int):
        super().__init__(budget)

    def select(self,
               population: Population[T]) -> Tuple[T]:
        """Greedy selection.

        Select the item in the population with highest fitness.
        """
        population.sort(lambda x: x.score)
        selected_solution = population[0]
        return (selected_solution,)


class ElitistSimpleSelector(SimpleSelector[T]):
    """Elitist selector that select the highest-fitness individual.

    Example for overriding `select_to_many`. Just overriding `select`
        is not enough, because elitism requires the highest-fitness
        individual of a _population_.
    """
    def __init__(self: Self, budget: int):
        super().__init__(budget-1)
        self.best_individual: Optional[T] = None

    def select_to_many(self, population: Population[T]) -> Tuple[T, ...]:
        """Context that implements elitism.

        Preserve and update an elite. Each time the selector is used, insert
            the current elite to the results.
        """
        results: Tuple[T, ...] = super().select_to_many(population)
        best_individual: Optional[T] = self.best_individual
        if best_individual is None:
            best_individual = results[0]
        for x in results:
            if x.score < best_individual.score:
                best_individual = x
        self.best_individual = best_individual

        return (*results, self.best_individual)


class TournamentSelector(Selector[T]):
    """Tournament selector.
    """
    def __init__(self: Self, budget: int, bracket_size: int = 2,
                 probability: float = 1):
        super().__init__(budget)
        self.bracket_size: int = bracket_size
        self.probability: float = min(2, max(probability, 0))

    def select(self,
               population: Population[T]) -> Tuple[T]:
        """Tournament selection.

        Select a uniform sample, then select the best member in that sample.
        """
        # Do not select if
        #   (a) the sample is less than bracket_size, or
        #   (b) the budget is less than bracket_size
        sample: List[T]
        if min(len(population), self.budget) < self.bracket_size:
            sample = list(population)
        else:
            sample = random.sample(tuple(population), self.bracket_size)
        sample.sort(key=lambda x: x.score, reverse=True)

        # If nothing is selected stochastically, select the last element
        selected_solution: T = sample[-1]

        # Select the ith element with probability p * (1-p)**i
        probability = self.probability
        for i in range(len(sample)):
            if random.random() < probability * (1 - probability)**i:
                selected_solution = sample[i]
                break

        return (selected_solution,)


def Elitist(sel: Selector[T]) -> Selector:  # type:ignore
    """Decorator that adds elitism to a selector.

    Modify `select_to_many` of `sel` to use elitism. If `sel` already
        overrides `select_to_many`, that implementation is destroyed.

    Args:
        sel: A selector

    Return:
        A selector
    """
    def select_to_many(self,
                       population: Population[T]) -> Tuple[Individual[T], ...]:
        """Context that implements elitism.
        """
        # Python magic. Since super() cannot be used in this context,
        #   directly call select_to_many in the parent.
        results: Tuple[Individual[T]] = self.__class__.__mro__[1].\
            select_to_many(self, population)  # type: ignore
        best_individual: Optional[Individual[T]] = self.best_individual
        if best_individual is None:
            best_individual = results[0]
        for x in results:
            if x.score > best_individual.score:
                best_individual = x
        self.best_individual = best_individual

        if self.best_individual is None:
            return (*results,)
        else:
            return (*results, best_individual)

    # Some say monkey patching is evil.
    # For others, _there is no good and evil, there is only power and those
    #   too weak to seek it.
    #       --  J.K. Rowling, Harry Potter and the Sorcerer's Stone_
    # This bad boy fails so many type checks.
    setattr(sel, 'best_individual', None)
    setattr(sel, 'select_to_many', MethodType(select_to_many, sel))
    return sel
