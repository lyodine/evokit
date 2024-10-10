from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .population import Individual, Population


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

    def select_to_many(self, population: Population[D]) -> tuple[D, ...]:
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
        return_list: list[D] = []
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
               population: Population[D]) -> tuple[D, ...]:
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
