from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any
    from .population import Tuple
    from .population import GenomePool

import abc
from abc import abstractmethod

from .population import Population
from .population import Genome


from typing import TypeVar
from typing import Generic

T = TypeVar("T", bound=Genome)

class ArityException(Exception):
    pass

class Variator(abc.ABC, Generic[T]):
    def __init__(self, arity: int, coarity: int) -> None:
        self.arity = arity
        self.coarity = coarity

    @abc.abstractmethod
    def vary(self, parents: Tuple[T, ...]) -> Tuple[T, ...]:
        """!Appy the variator to a tuple of parents
            Produce a tuple of genomes from a tuple of genomes.
            The input and output tuple sizes should match the arity and coarity of this selector, respectively.
            Implementation note: clear the score first.
        """
        pass

        # magic remove the Nones
    def vary_pool(self, pool: GenomePool[T], rate: Any = None, a=None, b=None) -> Population[T] :
        """!Apply the variator to a pool of tuples of parents.
            Also applies the "dynamic scoring" heuristic: the score of a genome is assigned to it as a field.
            Inspecting this field instead of evaluating the solution may save cost.
            @TODO This heuristic has caused several problems in implementation. One more moving piece.
        """
        new_population = Population[T]()
        for pair in pool:
            results = self.vary(pair)
            for individual in results:
                new_population.append(individual)

        return new_population
    
class DefaultVariator(Variator[T]):
    """!The default variator does not change anything
    s"""
    def __init__(self):
        super().__init__(1, 1, False)

    @abc.abstractmethod
    def vary(self, parents: Tuple[T, ...]) -> Tuple[T, ...]:
        e = []
        for x in parents:
            e.append(x)
        return tuple(e)
