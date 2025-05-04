from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Optional
    from typing import Sequence
    from .population import Tuple

import abc
from abc import abstractmethod
from typing import Generic, TypeVar

from .population import Individual, Population

T = TypeVar("T", bound=Individual)

class ArityException(Exception):
    pass

class Variator(abc.ABC, Generic[T]):
    def __init__(self, arity: int, coarity = None) -> None:
        self.arity: Optional[int] = arity
        self.coarity: Optional[int] = coarity

    @abc.abstractmethod
    def vary(self, parents: Tuple[T, ...]) -> Tuple[T, ...]:
        """Appy the variator to a tuple of parents

        Produce a tuple of individuals from a tuple of individuals.
        The input and output tuple sizes should match the arity and coarity of this selector, respectively.
            Implementation note: clear the score first.
        """
        pass

        # magic remove the Nones
    
    def _group_to_parents(self, population: Population[T])-> Sequence[Individual[T]]:
        # Tuple magic. Zipping an iterable with itself extracts a tuple of that size. The "discarding" behaviour is implemented this way.
        parent_groups: Sequence[int]
        if self.arity is None:
            raise ValueError("Variator does not specify arity, cannot create parent groups")
        else:
            parent_groups = tuple(zip(*(iter(population),) * self.arity))
        return parent_groups
            
    
    def vary_population(self, population: Population[T]) -> Population[T]:
        next_population = Population[T]()
        parent_groups: ... = self._group_to_parents(population)
        for group in parent_groups:
            results = self.vary(group)
            for individual in results:
                next_population.append(individual)
        return next_population
        
    
class DefaultVariator(Variator[T]):
    """!The default variator does not change anything
    """
    def __init__(self):
        super().__init__(1, 1)

    @abc.abstractmethod
    def vary(self, parents: Tuple[T, ...]) -> Tuple[T, ...]:
        e = []
        for x in parents:
            e.append(x)
        return tuple(e)
