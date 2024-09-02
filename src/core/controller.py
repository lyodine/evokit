""" The controller is an iterative optimizer that receives various evolutionary operators.
"""

from typing import get_args
from typing import Dict

from typing import Callable
from typing import Self
from typing import Optional
from typing import TypeVar
from typing import Generic

from .population import Population
from .population import Genome
from .population import GenomePool
from .evaluator import Evaluator
from .variator import Variator
from .selector import Selector

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
        self._ensure_operator_types()
        self.generation = 0

    def _ensure_operator_types(self):
        """!Assert that the population, the evaluator, the parent selector,
            the variator, and the offspring selector are correctly typed.
            @note This function does not check if operators have the correct
                type arguments. For example, it does not detect if an
                evaluator for binary strings and an variator for genetic
                programs are used together, only that the evaluator is an
                evaluator and the variator is an variator.
        """
        assert isinstance(self.population, Population)
        assert isinstance(self.evaluator, Evaluator)
        assert isinstance(self.parent_selector, Selector)
        assert isinstance(self.variator, Variator)
        assert isinstance(self.offspring_selector, Selector)

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
        survivors = self.survivor_selector.select_to_population(children)

        # The survivor become the next population.
        self.population = survivors

        # Returning self allows chaining multiple calls to `step`
        return self
    
    

    