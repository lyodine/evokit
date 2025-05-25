""" The controller is an iterative optimizer that receives various evolutionary operators.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self
    from .population import GenomePool
    from .evaluator import Evaluator
    from .variator import Variator
    from .selector import Selector
    from .population import Population

from .population import Genome
from typing import Generic
from typing import TypeVar

T = TypeVar("T", bound = Genome)

class Controller(Generic[T]):
    """The controller manages the learning process.
    """
    def __init__(self,
            population: Population[T],
            evaluator: Evaluator[T],
            parent_selector: Selector[T],
            variator: Variator[T],
            offspring_selector: Selector[T],
    ) -> None:
        """!Initialize an evolution controller with a set of configurable components.
            @param population: the initial population
            @param evaluator: The evaluator acts on an individual to determine its fitness.
            @param parent_selector: The parent selector applies to the population before variation. The range of the parent selector must match the domain of the variator.
            @param variator: The variator receives a collection of elements and outputs a list of genomes. These genomes are deposited into the population.
            @param offspring_selector: The parent selector that is applied before variation.
        """
        self.population = population
        self.evaluator = evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.offspring_selector = offspring_selector
        self.generation = 0

    def step(self) -> Self:
        """!Advance the population by one generation.
        """
        # Increment the generation count
        # The generation count begins at 0. Before the first generation,
        #   increment the count to 1.
        self.generation = self.generation + 1

        # Evaluate the population
        self.evaluator.evaluate_population(self.population)
        
        # Select from the population into the genome pool
        parents: GenomePool = self.parent_selector.select_to_pool(self.population)

        # Vary the genome pool to create offspring
        offspring = self.variator.vary_pool(parents, None)

        # Evaluate the offspring
        self.evaluator.evaluate_population(offspring)

        # Select from the offspring
        offspring = self.offspring_selector.select_to_population(offspring)

        # The survivor become the next population.
        self.population = offspring

        # Returning self allows chaining multiple calls to `step`
        return self
