# TODO Move Individual and Population to separate files.
#   The Java thing is a good practice. One might even say, best practice.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator
    from typing import Callable
    from typing import Optional
    from typing import Self
    from typing import Type
    from typing import Any
    from typing import Union

from typing import overload
from typing import Iterable
from typing import Sequence

import itertools
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

R = TypeVar('R')


class Individual(ABC, Generic[R]):
    """Base class for all individuals.

    Derive this class to create custom representations.
    """
    def __new__(cls: Type[Self], *args: Any, **kwargs: Any) -> Self:
        """Machinery. Implement managed attributes.

        :meta private:
        """
        instance: Self = super().__new__(cls)
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
            ValueError: if the current fitness is ``None``
        """
        # TODO: Consider letting fitness return None if it is not assigned,
        #   instead of raising an exception.
        # There should be a limit to hand-holding the developer,
        #   and this might be it.

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

        Set the fitness of the individual to ``None``.
        """
        self._fitness = None

    def has_fitness(self) -> bool:
        """Return if the genome has a fitness value.

        Return:
            ``False`` if the current :attr:`fitness` is ``None``, otherwise ``True``
        """
        return self._fitness is not None

    @abstractmethod
    def copy(self) -> Self:
        """Copy the solution.

        Subclasses should override this method.

        In addition to duplicating :attr:`genome`, the implementation
        should decide whether to retain other fields such as :attr:`fitness`.

        Returns:
            A new individual.

        Note:
            Ensure that changes made to the returned value do not affect
            the original value.
        """
        # TODO Some people do not how to do this -- link to an example
        #   to make this function more usable.


class AbstractCollection(ABC, Generic[R], Sequence[R], Iterable[R]):
    """Machinery.

    Data structure for collections that may be performance bottlecaps.
    TODO: I cannot find a way to document methods inherited from this class.
    """
    def __init__(self, *args: R):
        self._items = list(args)
        self._index = 0

    def __len__(self) -> int:
        return len(self._items)

    @overload
    def __getitem__(self, key: int) -> R:
        ...

    @overload
    def __getitem__(self, key: slice) -> Sequence[R]:
        ...

    def __getitem__(self, key: Union[int, slice]) -> R | Sequence[R]:
        return self._items[key]

    def __setitem__(self, key: int, value: R) -> None:
        self._items[key] = value

    def __delitem__(self, key: int) -> None:
        del self._items[key]

    def __str__(self) -> str:
        return str(list(map(str, self._items)))

    def __iter__(self) -> Iterator[R]:
        for i in range(len(self)):
            yield self[i]

    def __next__(self) -> R:
        if self._index < len(self._items):
            old_index = self._index
            self._index = self._index + 1
            return self._items[old_index]
        else:
            raise StopIteration

    def append(self, value: R) -> None:
        """Append an item to this collection

        Args:
            value: the item to add to this item
        """
        # TODO value is a really bad name
        self._items.append(value)

    def extend(self, values: Iterable[R]) -> None:
        """Append all items from another collection to this collection

        Args:
            values: collection whose values are appended to this collection
        """
        # TODO WOW list comprehension magic. Might be totally inefficient
        # though.
        # Remember that this class is a performance bottleneck.
        self._items = list(itertools.chain(self._items, values))

    def populate(self, new_data: Iterable[R]) -> None:
        """Remove items in this collection with all items from another
        collection.

        Args:
            values: collection whose values are appended to this collection
        """
        # TODO This method is defined but not used, as of 2024-04-02.
        #   It was added for "completeness". Completeness does not warrant
        #   redundancy.
        self._items = list(new_data)

    def draw(self, key: Optional[R] = None, pos: Optional[int] = None) -> R:
        """Remove an item.

        Identify an item either by value (in key) or by position (in pos).
        Remove that item from the collection, then return that value.

        Returns:
            The :class:`Individual` that is removed from the population
        Raises:
            TypeError: If neither ``key`` nor ``pos`` is given.
        """
        if (key is None and pos is None):
            raise TypeError("An item must be speccified, either by"
                            " value or by position. Neither is given.")
        elif (key is not None and pos is not None):
            raise TypeError("The item can only be specified by value"
                            "or by position. Both are given.")
        elif (pos is not None):
            a: R = self[pos]
            del self[pos]
            return a
        elif (key is not None):
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
        else:
            raise RuntimeError("Values of key and pos changed during evaluation")


D = TypeVar("D", bound=Individual)


class Population(AbstractCollection[D],
                 Sequence[D],
                 Iterable[D]):
    """A flat collection of individuals.
    """
    def __init__(self, *args: D):
        super().__init__(*args)

    def copy(self) -> Self:
        """Return an independent population.

        Changes made to items in the new population should not affect
        items in this population. This behaviour depends on correct implementation
        of `~.Individual.copy` in each item.

        Call `~.Individual.copy` for each :class:`Individual` in this
        population. Collect the results, then create a new population with
        these values.

        Returns:
            A new population.
        """
        return self.__class__(*[x.copy() for x in self._items])

    def sort(self: Self,
             ranker: Callable[[D], float] = lambda x: x.fitness) -> None:
        """Rearrange items by fitness, highest-first.

        The item at index 0 has the highest index.
        """
        # TODO Should I try-catch? Because accessing an individual
        #   without fitness throws an exception.
        self._items.sort(reverse=True, key=ranker)

    def reset_fitness(self: Self) -> None:
        """Remove fitness values of all Individuals in the population.

        """

        # TODO This behaviour exists in two places: in evaluators
        #   (which is responsible for cleaning offspring)
        #   and here. Discuss it.
        #   This is an old comment.
        for x in self._items:
            x.reset_fitness()

    def best(self: Self) -> D:
        best_individual: D = self[0]

        for x in self:
            if x.fitness > best_individual.fitness:
                best_individual = x

        return best_individual
