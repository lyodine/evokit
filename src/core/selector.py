from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Tuple
    from typing import List
    from typing import Optional
    from typing import Iterator
    from typing import Self

from .population import Population
from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import TypeVar

from .population import Genome
from .population import GenomePool

T = TypeVar("T", bound=Genome)

class Selector(ABC, Generic[T]):
    """!An abstract selector
        A selector that can be applied as a parent selector or a survivor selector.
    """

    def __init__(self: Self, coarity: int, budget: int):
        """!Initialise the selector
            @param coarity: {TODO} Hide this logic in the controller
        """
        self.coarity = coarity
        self.budget = budget

    def select_to_pool(self,
                       population: Population[T],
                       budget: Optional[int] = None) -> GenomePool[T]:
        """!Select to tuples of parents
            Select to a GenomePool instance, which can be passed to the variator. The arity of the returned value depends on the arity of the selector.
            If the population cannot exactly fill tuples of a given size, discard the left-over genomes.
            @postcondition: the returned population is descored
        """
        selected = self.select_to_many(population, budget)

        # Tuple magic. Zipping an iterable with itself extracts a tuple of that size. The "discarding" behaviour is implemented this way.
        ai:Iterator[T] = iter(selected)
        output_tuples:List[Tuple[T, ...]] = list(zip(*tuple(ai for i in range(self.coarity))))
        pool = GenomePool[T](self.coarity)

        for x in output_tuples:
            pool.append(x)
        return pool

    def select_to_population(self,
                             population: Population[T],
                             budget: Optional[int] = None) -> Population[T]:
        """!Select to a Population
            Select to a Population instance. This might happen, for example,
                while the selector is acting as a survivor selector.
            @postcondition: the returned population is descored
        """
        selected = self.select_to_many(population, budget)
        new_population = Population[T]()
        for x in selected:
            new_population.append(x)
        return new_population

    def select_to_many(self, population: Population[T], budget: Optional[int] = None) -> Tuple[T, ...]:
        """!Many-to-many selection strategy.
            Repeatedly apply select() to create a collection of solutions
            @param population: the input population
            @param evaluator: the evaluator that selects from the input population
            @param budget: the size of the returned collection.
        """

        old_population: Population[T] = population
        return_list: List[T] = []

        # ----- Budget -----
        # If a budget is not given, use my default budget
        if budget is None:
            budget = self.budget
        # The budget cannot exceed the population size
        budget = min(budget, len(old_population))

        # Keep selecting until the budget runs out.
        # The final selection might exceed the buedget. The selector must take care to not
        # cause weird stuff to happen.
        budget_used: int = 0
        while budget_used < budget:
            selected_results = self.select(old_population)
            # Remove results from the population
            # TODO This is an abuse of `draw`.
            [population.draw(x) for x in selected_results]
            return_list.append(*selected_results)
            budget_used = budget_used + len(selected_results)
        return tuple(return_list)

    @abstractmethod
    def select(self,
               parents: Population[T]) -> Tuple[T, ...]:
        """!Many-to-one selection strategy
            Select, possibly stochastically, a solution from the population
            @param parents: the input population
            @param evaluator: the evaluator that selects from the input population
            @sideeffect Each call takes one member from the input population
        """
        pass

class NullSelector(Selector[T]):
    def __init__(self: Self, coarity:int, budget: int):
        super().__init__(coarity, budget)

    def select_to_many(self, population: Population[T], budget: Optional[int] = None) -> Tuple[T, ...]:
        return tuple(x for x in population)

class SimpleSelector(Selector[T]):
    def __init__(self: Self, coarity:int, budget: int):
        super().__init__(coarity, budget)

    def select(self,
               population: Population[T])-> Tuple[T]:
        """!A one-to-one selection strategy.
            Select the solution with highest fitness.
        """
        population.sort(lambda x : x.score)
        selected_solution = population[0]
        return (selected_solution,)

class ElitistSimpleSelector(SimpleSelector[T]):
    def __init__(self: Self, coarity:int, budget: int):
        super().__init__(coarity, budget-1)
        self.best_genome: Optional[T] = None

    def select_to_many(self, population: Population[T], budget: Optional[int] = None) -> Tuple[T, ...]:
        """!A many-to-many selection strategy.
            Preserve and update an elite, insert the elite to the resulted population.
        """
        results: Tuple[T, ...] = super().select_to_many(population, budget)
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
    def __init__(self: Self, coarity:int, budget: int, bracket_size:int = 2, probability:float = 1):
        super().__init__(coarity, budget)
        self.bracket_size: int = bracket_size
        self.probability: float = min(2, max(probability, 0))

    def select(self,
               population: Population[T])-> Tuple[T]:
        """!A one-to-one selection strategy.
            Select a uniform sample, then select the best member
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

import types

def Elitist(sel: Selector[T])-> Selector:
    # TODO This is an adapter.
    # Please don't
    def select_to_many(self, population: Population[T], budget: Optional[int] = None) -> Tuple[T, ...]:
        # Python magic. Since super() cannot be used in this context,
        #   directly call select_to_many in the parent.

        results: Tuple[T, ...] = self.__class__.__mro__[1].select_to_many(self, population, budget)
        best_genome: Optional[T] = self.best_genome
        if best_genome is None:
            best_genome = results[0]
        for x in results:
            if x.score > best_genome.score:
                best_genome = x



        self.best_genome = best_genome
        return (*results, self.best_genome)

    setattr(sel, 'best_genome', None)
    setattr(sel, 'select_to_many', types.MethodType(select_to_many, sel))
    return sel
