# TODO Move Individual and Population to separate files.
#   The Java thing is a good practice. One might even say, best practice.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator
    from typing import Iterable
    from typing import Callable
    from typing import Optional
    from typing import Self

import itertools
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

R = TypeVar('R')


class Individual(ABC, Generic[R]):
    """Base class for all individuals.

    Derive this class to create custom representations.
    """
    def __new__(cls, *args, **kwargs):
        """Machinery. Implement managed attributes.

        :meta private:
        """
        instance = super().__new__(cls)
        instance._fitness = None
        return instance
    
    @abstractmethod
    def __init__(self) -> None:
        #: Fitness of the individual
        self._fitness: Optional[float]
        #: Genotype of the individual. Subclasses should store
        #  the representation in this attribute.
        # TODO Think about a better way to put it, "contained value"?
        #   surely "value" is too general.
        self.genome: Optional[R] = None

    @property
    def fitness(self) -> float:
        """Fitness of an individual.

        Writing to this property changes the fitness of the individual.
        Reading this property may raise an exception, if a fitness has
        not been assigned.

        Return:
            Fitness of the individual

        Raise:
            ValueError if the current fitness is `None`
        """
        # TODO: Consider letting fitness return None if it is not assigned,
        #   instead of raising an exception.
        # There should be a limit to hand-holding the developer, and this might be it.

        if (self._fitness is None):
            raise ValueError("Score is accessed but null")
        else:
            return self._fitness

    @fitness.setter
    def fitness(self, value: float) -> None:
        """Sphinx does not register docstrings on setters.
        """
        self._fitness = value

    def reset_fitness(self) -> None:
        """Reset the fitness of the individual.

        Set the fitness of the individual to None, as if it has not been
        evaluated.
        """
        self._fitness = None

    def has_fitness(self) -> bool:
        """Return if the genome has a fitness value.

        Return:
            False if the fitness of the genome is None, otherwise return True
        """
        return self._fitness is not None

    @abstractmethod
    def copy(self) -> Self:
        """Copy the solution.

        All subclasses should override this method. In addition to duplicating
        :attr:`genome`, the implementation should decide if other fields
        such as :attr:`fitness` should be retained.

        Todo:
            Rephrase.

        Returns:
            A new individual.

        Note:
            The implementationn should ensure that changes made to the
            return value do not affect the original value.
        """
        # TODO Some people do not how to do this -- link to an example
        #   to make this function more usable.

T = TypeVar('T', bound=Individual)

class AbstractCollection(ABC, Generic[R]):
    """Machinery. Data structure for collections that may be
    performance bottlecaps.
    
    :meta private:
    """
    def __init__(self, *args: R):
        self._solutions = list(args)
        self._index = 0

    def __len__(self) -> int:
        return len(self._solutions)

    def __getitem__(self, key: int) -> R:
        return self._solutions[key]

    def __setitem__(self, key: int, value: R) -> None:
        self._solutions[key] = value

    def __delitem__(self, key: int) -> None:
        del self._solutions[key]

    def __str__(self) -> str:
        return str(list(map(str, self._solutions)))

    def __iter__(self) -> Iterator[R]:
        self._index = 0
        return self

    def __next__(self) -> R:
        if self._index < len(self._solutions):
            old_index = self._index
            self._index = self._index + 1
            return self._solutions[old_index]
        else:
            raise StopIteration

    def append(self, value: R) -> None:
        """Append an item to this collection

        Args:
            value: the item to add to this item
        """
        # TODO value is a really bad name
        self._solutions.append(value)

    def extend(self, values: Iterable[R]) -> None:
        """Append all items from another collection to this collection

        Args:
            values: collection whose values are appended to this collection
        """
        # TODO WOW list comprehension magic. Might be totally inefficient
        # though.
        # Remember that this class is a performance bottleneck.
        self._solutions = list(itertools.chain(self._solutions, values))

    def populate(self, new_data: Iterable[R]) -> None:
        """Remove items in this collection with all items from another
        collection.

        Args:
            values: collection whose values are appended to this collection
        """
        # TODO This method is defined but not used, as of 2024-04-02.
        #   It was added for "completeness". Completeness does not warrant
        #   redundancy.
        self._solutions = list(new_data)

    def draw(self, key: int | R) -> R:
        if isinstance(key, int):
            a: R = self[key]
            del self[key]
            return a
        else:
            has_removed = False
            # TODO refactor with enumerate and filter.
            #   Still up for debate. Loops are easy to understand.
            #   One must consider the trade-off.
            for i in range(len(self)):
                # Development mark: delete the exception when I finish this
                if self[i] == key:
                    has_removed = True
                    del self[i]
                    break

            if (not has_removed):
                raise IndexError("the requested item is not in the list")
            else:
                return key


class Population(AbstractCollection[T]):
    """A flat collection of individuals.
    """
    def __init__(self, *args: T):
        super().__init__(*args)

    def copy(self) -> Self:
        """Returns an independent population.
        TODO Following the issue raised in Individual: be sure to
        make explicit behaviours of this copy, and its guarantees.
        """
        return self.__class__(*[x.copy() for x in self._solutions])

    def sort(self: Self,
             ranker: Callable[[T], float] = lambda x: x.fitness) -> None:
        """Sort items in this report
            TODO The process accesses _score_ in individuals, which may
            cause an error, according to the "current" implementation
            as of 2024-04-01.
            If the reporter is in _score_, then leave a try catch clause to
            make this explicit. Otherwise, don't care.
        """
        self._solutions.sort(reverse=True, key=ranker)

    def descore(self: Self) -> None:
        """Clean the score of all Individuals in the population.
            TODO This behaviour exists in two places: in evaluators
            (which is responsible for cleaning offspring)
            and here. Discuss it.
        """
        for x in self._solutions:
            x.reset_fitness()
