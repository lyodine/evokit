from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from typing import Sequence
    from typing import Iterable

from abc import ABC
from typing import Generic, TypeVar, Any
from .population import Individual, Population


D = TypeVar("D", bound=Individual[Any])


class Selector(ABC, Generic[D]):
    """Base class for all selectors.

    Derive this class to create custom selectors.

    Tutorial: :doc:`../guides/examples/selector`.
    """

    def __init__(self: Self,
                 budget: int,
                 *args: Any,
                 **kwargs: Any,):
        """
        Args:
            budget: Number of individuals to select.

        .. note::
            Implementations that select a variable number of
            individuals may ignore :attr:`.budget`.
        """
        #: Declared size of the output population.
        self.budget = budget

    def select_population(self: Self,
                          from_population: Population[D],
                          *args: Any,
                          **kwargs: Any) -> Population[D]:
        """Select from a population to a population.

        The default implementation calls :meth:`select` on
        :arg:`from_population` and collects the results.

        All subclasses should override either this method or :meth:`.select`.
        Consider overriding this method if selection requires information
        about the whole population. Example: fitness proportionate selection.

        Args:
            from_population: Population to select from.

        .. warning::

            The default implementation calls :meth:`.select` as long as
            the number of selected individuals is less than :attr:`.budget`.

            As such, if :meth:`.select` can return multiple individuals, then
            the last call may return more individuals than what the budget
            permits.
        """
        # The budget must not exceed the population size.
        # The cap is the minimum of ``self.budget`` and ``len(population)``.
        budget_cap = min(self.budget, len(from_population))

        def _generate_results() -> Iterable[D]:
            """Local function.

            While the number of selected individuals is less than
            ``budget_cap``, :meth:`select` from ``population`` and
            accumulate the results.
            """

            budget_used: int = 0

            while budget_used < budget_cap:
                selected_results: tuple[D, ...] = self.select(from_population)
                budget_used += len(selected_results)
                yield from selected_results

        return Population(list(_generate_results()))

    def select(self: Self,
               from_pool: Sequence[D],
               *args: Any,
               **kwargs: Any) -> tuple[D, ...]:
        """Select individuals from a sequence of individuals.

        All subclasses should override either this method or
        :meth:`select_population`.

        Args:
            from_pool: Tuple of individuals to select from.

        .. note::
            Each item in the returned tuple must be in :arg:`from_pool`.

            The selector should treat higher fitness as "better".
            Assume that :class:`.Evaluator`\\ s assign higher
            fitness to better individuals.

        Raise:
            NotImplementedError: If the subclass does not override this
                method.
        """
        raise NotImplementedError("This method is not implemented.")
