from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from typing import Sequence
    from typing import Self
    from typing import Type

from abc import abstractmethod
from abc import ABC
from typing import Any
from typing import Generic, TypeVar

from .population import Individual, Population
from typing import override

D = TypeVar("D", bound=Individual[Any])


class Variator(ABC, Generic[D]):
    """Base class for all selectors.

    Derive this class to create custom selectors.

    Tutorial: :doc:`../guides/examples/onemax`.
    """

    def __new__(cls: Type[Self], *args: Any, **kwargs: Any) -> Self:
        """Machinery.

        :meta private:
        """
        instance: Self = super().__new__(cls)

        #: Size of input to :meth:`vary`
        instance.arity = None

        return instance

    def __init__(self: Self) -> None:
        #: Size of input to :meth:`vary`
        self.arity: Optional[int]

    @abstractmethod
    def vary(self, parents: Sequence[D]) -> tuple[D, ...]:
        """Apply the variator to a tuple of parents

        Produce a tuple of individuals from a sequence of individuals.

        The length :arg:`.parents` is at most :attr:`.arity`.
        """
        pass

    def _group_to_parents(self,
                          population: Population[D])\
            -> Sequence[Sequence[D]]:
        """Machinery.

        :meta private:

        Divide the population into sequences of the given size.
        """
        # Tuple magic. Zipping an iterable with itself extracts a tuple of
        #   that size. The "discarding" behaviour is implemented this way.
        parent_groups: Sequence[Sequence[D]]
        if self.arity is None:
            raise TypeError("Variator does not specify arity,"
                            "cannot create parent groups")
        else:
            parent_groups = tuple(zip(*(iter(population),) * self.arity))
        return parent_groups

    def vary_population(self: Self,
                        population: Population[D]) -> Population[D]:
        """Vary the population.

        The default implementation separates ``population`` into groups
        of size `.arity`, call `.vary` with each group as argument,
        then collect and returns the result.

        Note:
            The default implementation calls :meth:`.Individual.reset_fitness`
            on each offspring to clear its fitness. Any implementation that
            overrides this method should do the same.
        """
        next_population = Population[D]()
        parent_groups: Sequence[Sequence[D]] =\
            self._group_to_parents(population)
        for group in parent_groups:
            results = self.vary(group)
            for individual in results:
                individual.reset_fitness()
                next_population.append(individual)
        return next_population


class NullVariator(Variator[D]):
    """Variator that does not change anything
    """
    def __init__(self) -> None:
        self.arity = 1

    @override
    def vary(self, parents: Sequence[D]) -> tuple[D, ...]:
        return tuple(parents)
