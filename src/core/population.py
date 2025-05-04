# TODO Move Genome, GenomePool, and Population to separate files.
#   The Java thing is a good practice. One might even say, best practice.

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Iterator
    from typing import Iterable
    from typing import Callable
    from typing import Optional
    from typing import Self

from typing import Tuple

from typing import Generic
from typing import TypeVar
import itertools

from abc import ABC
from abc import abstractmethod

from math import inf

R = TypeVar('R')

# TODO Consider if the exception should be raised from:
#   - the user (evaluator, which must handle none values), or
#   - the "used" (Genome, which reports if the value is none but accessed)
class NullScoreException(Exception):
    pass

class Genome(ABC, Generic[R]):
    """!A solution
        A genotypical representation of a solution that specifies the
        capabilities a solution must have in order to work with evolutionary operators.
    """
    def __init__(self) -> None:
        # The genome
        self._score: Optional[float] = None

    @property
    def score(self)-> float:
        """!Return the score that has been assigned to this genome.
            Raise an NullScoreException if the score has not been assigned.
        TODO consider refactoring this method into a getter.
            Because apparently Python can do that.
        @return
        @raise
        """
        if (self._score is None):
            raise NullScoreException("Score is accessed but null")
        else:
            return self._score

    @score.setter
    def score(self, value: float)-> None:
        self._score = value

    def descore(self)-> None:
        self._score = None

    def is_scored(self)-> bool:
        return self._score is not None

    @abstractmethod
    def copy(self) -> Self:
        """!Copy the solution.
            Copy the solution, so that changes made on the copy do not affect the original genome.
            The implementation decides if all components must be copied.
        """

T = TypeVar('T', bound=Genome)

class AbstractCollection(ABC, Generic[R]):
    """!An abstract collection of things. Provides the behaviour of other collections. Improving it will surely lead to improvement in overall performance of the model.
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
            @param value the item to add to this item
        """
        # TODO value is a really bad name
        self._solutions.append(value)

    def extend(self, values: Iterable[R])-> None:
        """Append all items from another collection to this collection
            @param values collection whose values are appended to this collection
        """
        # TODO WOW list comprehension magic. Might be totally inefficient though.
        # Remember that this class is a performance bottleneck.
        self._solutions = list(itertools.chain(self._solutions, values))

    def populate(self, new_data: Iterable[R])-> None:
        """Remove items in this collection with all items from another collection.
            @param values collection whose values are appended to this collection
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

class GenomePool(AbstractCollection[Tuple[T, ...]]):
    """!A collection of tuple  of parents.
        A collection of tuples of solutions.
        Passed from the parent selector to the variator. Its arity is not enforced.
    """
    def __init__(self, arity: int, *args: Tuple[T, ...]):
        super().__init__(*args)
        self.arity = arity

    def descore(self)-> None:
        for t in self._solutions:
            for x in t:
                x.descore()

    def get_best_score(self)-> float:
        best_score = -inf
        for t in self:
            for tt in t:
                if tt.score > best_score:
                    best_score = tt.score
        return best_score

class Population(AbstractCollection[T]):
    """!A collection of solutions.
        A population of many genomes.
    """
    def __init__(self, *args: T):
        super().__init__(*args)

    def copy(self) -> Self:
        """Returns an independent population.
        TODO Following the issue raised in Genome: be sure to
            make explicit behaviours of this copy, and its guarantees.
        """
        return self.__class__(*[x.copy() for x in self._solutions])

    def sort(self: Self, ranker: Callable[[T], float] = lambda x : x.score)-> None:
        """Sort items in this report
            TODO The process accesses _score_ in genomes, which may
            cause an error, according to the "current" implementation
            as of 2024-04-01.
            If the reporter is in _score_, then leave a try catch clause to
                make this explicit.
            Otherwise, don't care.
        """
        self._solutions.sort(reverse=True, key=ranker)

    def descore(self: Self)-> None:
        """Clean the score of all Genomes in the population.
            TODO This behaviour exists in two places: in evaluators
                (which is responsible for cleaning offspring)
                and here. Discuss it.
        """
        for x in self._solutions:
            x.descore()



