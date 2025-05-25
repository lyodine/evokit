from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Tuple
    from typing import List
    from typing import Optional
    from typing import Iterator
    from typing import Self

from types import MethodType

from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import TypeVar
from .population import Population
from .population import Genome
from .population import GenomePool

T = TypeVar("T", bound=Genome)

class Selector(ABC, Generic[T]):
    """Base class for all selectors.

    Derive this class to create custom selectors.
    """

    def __init__(self: Self, budget: int):
        """
        Args:
            budget: Number of genomes in the output.
        """
        self.budget = budget

    def select_to_pool(self,
                       population: Population[T],
                       coarity: int) -> GenomePool[T]:
        """As a parent selector, select from a population to a parent pool.

        Args:
            population: population to select from.
            coarity: size of each parent tuple in the output.

        Notes:
            If the population cannot exactly fill tuples of a given size, discard the left-over genomes.

        Todo:
            the returned population is descored?
            Not so sure about that - I cannot find the code that descores the population.
        """
        selected = self.select_to_many(population)

        # Tuple magic. Zipping an iterable with itself extracts a tuple of that size. The "discarding" behaviour is implemented this way.
        ai:Iterator[T] = iter(selected)
        output_tuples:List[Tuple[T, ...]] = list(zip(*tuple(ai for i in range(coarity))))
        pool = GenomePool[T](coarity)

        for x in output_tuples:
            pool.append(x)
        return pool

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
            for x in selected_results: population.draw(x)
            return_list.append(*selected_results)
            budget_used = budget_used + len(selected_results)
        return tuple(return_list)

    @abstractmethod
    def select(self,
               population: Population[T]) -> Tuple[T, ...]:
        """Selection strategy of the selector.

        All subclasses should override this method. The implementation should
            return a tuple of genomes. Each item in the tuple should also
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
               population: Population[T])-> Tuple[T]:
        """Greedy selection.

        Select the item in the population with highest fitness.
        """
        population.sort(lambda x : x.score)
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
        self.best_genome: Optional[T] = None

    def select_to_many(self, population: Population[T]) -> Tuple[T, ...]:
        """Context that implements elitism.

        Preserve and update an elite. Each time the selector is used, insert
            the current elite to the results.
        """
        results: Tuple[T, ...] = super().select_to_many(population)
        best_genome: Optional[T] = self.best_genome
        if best_genome is None:
            best_genome = results[0]
        for x in results:
            if x.score < best_genome.score:
                best_genome = x
        self.best_genome = best_genome

        return (*results, self.best_genome)

import random
class TournamentSelector(Selector[T]):
    """Tournament selector.
    """
    def __init__(self: Self, budget: int, bracket_size:int = 2, probability:float = 1):
        super().__init__(budget)
        self.bracket_size: int = bracket_size
        self.probability: float = min(2, max(probability, 0))

    def select(self,
               population: Population[T])-> Tuple[T]:
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
        sample.sort(key = lambda x : x.score, reverse=True)

        # If nothing is selected stochastically, select the last element
        selected_solution: T = sample[-1]

        # Select the ith element with probability p * (1-p)**i
        probability = self.probability
        for i in range(len(sample)):
            if random.random() < probability * (1 - probability)**i:
                selected_solution = sample[i]
                break

        return (selected_solution,)

def Elitist(sel: Selector[T])-> Selector: #type:ignore
    """Decorator that adds elitism to a selector.

    Modify `select_to_many` of `sel` to use elitism. If `sel` already
        overrides `select_to_many`, that implementation is destroyed.

    Args:
        sel: A selector

    Return:
        A selector
    """
    def select_to_many(self, population: Population[T], budget: Optional[int] = None) -> Tuple[T, ...]:
        """Context that implements elitism.
        """
        # Python magic. Since super() cannot be used in this context,
        #   directly call select_to_many in the parent.
        results: Tuple[T, ...] = self.__class__.__mro__[1].select_to_many(self, population)
        best_genome: Optional[T] = self.best_genome
        if best_genome is None:
            best_genome = results[0]
        for x in results:
            if x.score > best_genome.score:
                best_genome = x
        self.best_genome = best_genome
        return (*results, self.best_genome)

    # Some say monkey patching is evil.
    # For others, _there is no good and evil, there is only power and those too weak to seek it.
    #       --  J.K. Rowling, Harry Potter and the Sorcerer's Stone_
    # This bad boy fails so many type checks.
    setattr(sel, 'best_genome', None)
    setattr(sel, 'select_to_many', MethodType(select_to_many, sel))
    return sel
