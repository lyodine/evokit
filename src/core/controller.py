""" The controller is an iterative optimizer that receives various evolutionary operators.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from .evaluator import Evaluator
    from .variator import Variator
    from .selector import Selector
    from .population import Population
    from .accountant import Accountant

from enum import Flag, auto
from typing import Generic, TypeVar

from .population import Individual

T = TypeVar("T", bound = Individual)

class ControllerEvent(Flag):
    INITIALISATION = auto()
    GENERATION_BEGIN = PRE_PARENT_EVALUATION = auto()
    PRE_PARENT_SELECTION = POST_PARENT_EVALUATION = auto()
    PRE_VARIATION = POST_PARENT_SELECTION = auto()
    PRE_SURVIVOR_EVALUATION = POST_VARIATION = auto()
    PRE_SURVIVOR_SELECTION = POST_SURVIVOR_EVALUATION = auto()
    GENERATION_END = POST_SURVIVOR_SELECTION = auto()

class Controller(Generic[T]):
    """Controller that manages the learning process.
    """
    def __init__(self,
            population: Population[T],
            evaluator: Evaluator[T],
            parent_selector: Selector[T],
            variator: Variator[T],
            offspring_selector: Selector[T],
    ) -> None:
        """
        Args:
            population: The initial population
            evaluator: The evaluator acts on an individual to determine its fitness.
            parent_selector: The parent selector applies to the population before variation. The range of the parent selector must match the domain of the variator.
            variator: The variator receives a collection of elements and outputs a list of individuals. These individuals are deposited into the population.
            offspring_selector: The parent selector that is applied before variation.
        """
        self.population = population
        self.evaluator = evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.offspring_selector = offspring_selector
        self.generation = 0
        self.accountants = []

    def step(self) -> Self:
        """Advance the population by one generation.
        """
        # Increment the generation count
        # The generation count begins at 0. Before the first generation,
        #   increment the count to 1.
        self.generation = self.generation + 1
        
        self.update(ControllerEvent.GENERATION_BEGIN)

        # Evaluate the population
        self.evaluator.evaluate_population(self.population)

        self.update(ControllerEvent.PRE_PARENT_SELECTION)
        
        # Select from the population into a new population
        parents: Population = self.parent_selector.select_to_population(self.population)

        self.update(ControllerEvent.PRE_VARIATION)

        # Vary the population to create offspring
        offspring = self.variator.vary_population(parents)

        self.update(ControllerEvent.PRE_SURVIVOR_EVALUATION)

        # Evaluate the offspring
        self.evaluator.evaluate_population(offspring)

        self.update(ControllerEvent.PRE_SURVIVOR_SELECTION)

        # Select from the offspring
        offspring = self.offspring_selector.select_to_population(offspring)

        # The survivor become the next population.
        self.population = offspring

        self.update(ControllerEvent.GENERATION_END)

        # Returning self allows chaining multiple calls to `step`
        return self
    
    def attach(self,accountant: Accountant):
        self.accountants.append(accountant)
        accountant.register(self)

    def update(self, event: ControllerEvent):
        for acc in self.accountants: acc.update(event)
    

# One main problem is that some members are unavailable at some points:
#   for example, the population is dry after parent selection.
# Also, there is the ned for "stocK" accountants.