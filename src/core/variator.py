from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from typing import Sequence
    from typing import Tuple
    from typing import Self

from abc import abstractmethod
from abc import ABC
from typing import Generic, TypeVar

from .population import Individual, Population
from typing import override

D = TypeVar("D", bound=Individual)


class Variator(ABC, Generic[D]):
    def __init__(self: Self,
                 arity: int,
                 coarity: Optional[int] = None) -> None:
        self.arity: Optional[int] = arity
        self.coarity: Optional[int] = coarity

    @abstractmethod
    def vary(self, parents: Sequence[D]) -> Tuple[D, ...]:
        """Appy the variator to a tuple of parents

        Produce a tuple of individuals from a tuple of individuals.
        The input and output tuple sizes should match the arity and coarity of
        this selector, respectively.
        Implementation note: clear the score first.
        """
        pass

    def _group_to_parents(self,
                          population: Population[D])\
            -> Sequence[Sequence[D]]:
        """Machinery.
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

    def vary_population(self: Self, population: Population[D]) -> Population[D]:
        next_population = Population[D]()
        parent_groups: Sequence[Sequence[D]] =\
            self._group_to_parents(population)
        for group in parent_groups:
            results = self.vary(group)
            for individual in results:
                next_population.append(individual)
        return next_population


class DefaultVariator(Variator[D]):
    """Variator that does not change anything
    """
    def __init__(self) -> None:
        super().__init__(1, 1)

    @override
    def vary(self, parents: Sequence[D]) -> Tuple[D, ...]:
        return tuple(parents)
