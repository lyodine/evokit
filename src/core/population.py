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
from math import inf
from typing import Generic, Tuple, TypeVar

R = TypeVar('R')

class Individual(ABC, Generic[R]):
    """Base class for all individuals.

    Representation of a solution. 

        Todo: find the right name, is it a representation, an individual,
            a solution, a individual, or just the genotype (since it does not implement a behaviour)?
    """
    def __init__(self) -> None:
        # The individual has a score
        self._score: Optional[float] = None

    @property
    def score(self)-> float:
        """Return the fitness that has been assigned to this individual.
        
        Raise an NullScoreException if the score has not been assigned.

        Return:
            Fitness of the individual

        Raise:
            ValueError if the score is accessed when it is `None`

        Todo: rename to fitness

        """
        if (self._score is None):
            raise ValueError("Score is accessed but null")
        else:
            return self._score

    @score.setter
    def score(self, value: float)-> None:
        """Set the fitness of the individual.
        Args:
            value: new fitness.
        """
        self._score = value

    def descore(self)-> None:
        """Reset the fitness of the individual.

        Set the fitness of the individual to None, as if it has not been evaluated.
        """
        self._score = None

    def is_scored(self)-> bool:
        return self._score is not None

    @abstractmethod
    def copy(self) -> Self:
        """Copy the solution.

        All subclasses should override this method. The implementation should
            prevent changes made on the result from affecting the original
            individual.
        """

T = TypeVar('T', bound=Individual)

class AbstractCollection(ABC, Generic[R]):
    """An abstract collection of things.
    
    Provides the behaviour of other collections.
    Improving it will surely lead to improvement in overall performance of the framework.
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

    def extend(self, values: Iterable[R])-> None:
        """Append all items from another collection to this collection
        
        Args:
            values: collection whose values are appended to this collection
        """
        # TODO WOW list comprehension magic. Might be totally inefficient though.
        # Remember that this class is a performance bottleneck.
        self._solutions = list(itertools.chain(self._solutions, values))

    def populate(self, new_data: Iterable[R])-> None:
        """Remove items in this collection with all items from another collection.
        
        Args:
            values: collection whose values are appended to this collection
        """
        # TODO This method is defined but not used, as of 2024-04-02.
        #   It was added for "completeness". Completeness does not warrant redundancy.
        self._solutions = list(new_data)

    def draw(self, key: int | R) -> R:
        if isinstance(key, int):
            a : R = self[key]
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

    def sort(self: Self, ranker: Callable[[T], float] = lambda x : x.score)-> None:
        """Sort items in this report
            TODO The process accesses _score_ in individuals, which may
            cause an error, according to the "current" implementation
            as of 2024-04-01.
            If the reporter is in _score_, then leave a try catch clause to
                make this explicit.
            Otherwise, don't care.
        """
        self._solutions.sort(reverse=True, key=ranker)

    def descore(self: Self)-> None:
        """Clean the score of all Individuals in the population.
            TODO This behaviour exists in two places: in evaluators
                (which is responsible for cleaning offspring)
                and here. Discuss it.
        """
        for x in self._solutions:
            x.descore()



