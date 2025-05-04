""" The controller is an iterative optimizer that receives various
    evolutionary operators.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from typing import List
    from .evaluator import Evaluator
    from .variator import Variator
    from .selector import Selector
    from .population import Population
    from .accountant import Accountant

from enum import Flag, auto
from typing import Generic, TypeVar

from .population import Individual

T = TypeVar("T", bound=Individual)

class Controller(Generic[T]):
    """Controller that manages the learning process.
    """
    def __init__(self,
                 population: Population[T],
                 evaluator: Evaluator[T],
                 parent_selector: Selector[T],
                 variator: Variator[T],
                 offspring_selector: Selector[T]) -> None:
        """
        Args:
            population: initial population.

            evaluator: operator that evaluate the fitness of an individual.

            parent_selector: operator that selects individuals for variation.

            variator: operator that creates new individuals from existing
            ones.

            offspring_selector: operator that selects to the next generation.
        """
        self.population = population
        self.evaluator = evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.offspring_selector = offspring_selector
        self.generation = 0
        self.accountants: List[Accountant] = []
        self.events: List[str] = ["GENERATION_BEGIN",
                                  "PRE_PARENT_SELECTION",
                                  "PRE_VARIATION",
                                  "PRE_SURVIVOR_EVALUATION",
                                  "PRE_SURVIVOR_SELECTION",
                                  "GENERATION_END"]

    def step(self) -> Self:
        """Advance the population by one generation.
        """
        # Increment the generation count
        # The generation count begins at 0. Before the first generation,
        #   increment the count to 1.
        self.generation = self.generation + 1

        self.update("GENERATION_BEGIN")

        # Evaluate the population
        self.evaluator.evaluate_population(self.population)

        self.update("PRE_PARENT_SELECTION")

        # Select from the population into a new population
        parents: Population[T] = self.parent_selector.select_to_population(
            self.population)

        self.update("PRE_VARIATION")

        # Vary the population to create offspring
        offspring = self.variator.vary_population(parents)

        self.update("PRE_SURVIVOR_EVALUATION")

        # Evaluate the offspring
        self.evaluator.evaluate_population(offspring)

        self.update("PRE_SURVIVOR_SELECTION")

        # Select from the offspring
        offspring = self.offspring_selector.select_to_population(offspring)

        # The survivor become the next population.
        self.population = offspring

        self.update("GENERATION_END")

        # Returning self allows chaining multiple calls to `step`
        return self

    def attach(self: Self, accountant: Accountant)-> None:
        self.accountants.append(accountant)
        accountant.register(self)

    def update(self, event: str) -> None:
        if event not in self.events:
            raise ValueError(f"Controller reports unregistered event {event}."
                             f"Add {event} to the controller's .events value")
        for acc in self.accountants:
            acc.update(event)


# One main problem is that some members are unavailable at some points:
#   for example, the population is dry after parent selection.
# Also, there is the ned for "stocK" accountants.
