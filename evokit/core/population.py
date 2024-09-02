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
    from typing import Tuple
    from typing import Dict
from functools import wraps

from typing import overload
from typing import Iterable
from typing import Sequence

import itertools
from abc import ABC, abstractmethod, ABCMeta
from typing import Generic, TypeVar

R = TypeVar('R')


class MetaGenome(ABCMeta):
    """Machinery. Implement special behaviours in :class:`Individual`.

    :meta private:
    """
    def __new__(mcls: Type, name: str, bases: Tuple[type],
                namespace: Dict[str, Any]) -> Any:  # `Any` is BAD
        ABCMeta.__init__(mcls, name, bases, namespace)

        def wrap_function(custom_copy: Callable[[Individual], Individual]) -> Callable:
            @wraps(custom_copy)
            def wrapper(self: Individual,
                        *args: Any, **kwargs: Any) -> Individual:
                custom_copy_result: Individual
                if self.has_fitness():
                    old_fitness = self.fitness
                    custom_copy_result = custom_copy(self, *args, **kwargs)
                    custom_copy_result.fitness = old_fitness
                else:
                    custom_copy_result = custom_copy(self, *args, **kwargs)
                return custom_copy_result
            return wrapper

        namespace["copy"] = wrap_function(
            namespace.setdefault("copy", lambda: None)
        )
        return type.__new__(mcls, name, bases, namespace)


class Individual(ABC, Generic[R], metaclass=MetaGenome):
    """Base class for all individuals.

    Derive this class to create custom representations.

    Note:
        An implementation should store the genotype in :attr:`.genome`.

        The individual can information outside of the genotype, such as a
        `.fitness`, a reference to the parent, and strategy parameter(s).

    Tutorial: :doc:`../guides/examples/onemax`.
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
        #: Fitness of the individual.
        self._fitness: Optional[float]

        #: Genotype of the individual.
        self.genome: R

    @property
    def fitness(self) -> float:
        """Fitness of an individual.

        Writing to this property changes the fitness of the individual.
        If this individual has yet to be assigned a fitness, reading
        from this property raises an exception.

        To determine if the individual has a fitness, call
        :meth:`has_fitness`.

        Return:
            Fitness of the individual

        Raise:
            :class:`ValueError`: if the current fitness is ``None``.
        """

        if (self._fitness is None):
            raise ValueError("Score is accessed but null")
        else:
            return self._fitness

    @fitness.setter
    def fitness(self, value: float) -> None:
        """Sphinx does not pick up docstrings on setters.

        This docstring should never be seen.

        Arg:
            Whatever.
        """
        self._fitness = value

    def reset_fitness(self) -> None:
        """Reset the fitness of the individual.

        Set the :attr:`.fitness` of the individual to ``None``.

        Effect:
            The `.fitness` of this individual becomes ``None``.
        """
        self._fitness = None

    def has_fitness(self) -> bool:
        """Return if the individual has a fitness value.
        """
        return self._fitness is not None

    @abstractmethod
    def copy(self) -> Self:
        """Return an identical copy of the individual.

        Subclasses should override this method.

        Operations on in this individual should not affect the new individual.
        In addition to duplicating :attr:`.genome`, the implementation should
        decide whether to retain other fields such as :attr:`.fitness`.

        Note:
            Ensure that changes made to the returned value do not affect
            the original value.
        """


class AbstractCollection(ABC, Generic[R], Sequence[R], Iterable[R]):
    """Machinery.
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
        """Append an item to this collection.

        Args:
            value: The item to add to this item
        """
        # TODO value is a really bad name
        self._items.append(value)

    def extend(self, values: Iterable[R]) -> None:
        """Append all items from another collection to this collection

        Args:
            values: Collection whose values are appended to this collection.
        """
        # TODO Inefficient list comprehension. Looks awesome though.
        # Improve at my own convenience.
        self._items = list(itertools.chain(self._items, values))

    def populate(self, new_data: Iterable[R]) -> None:
        """Replace items in this population with items in :arg:`new_data`.

        Args:
            new_data: Collection whose items replace items in this
                population.

        Effect:
            Replace all items in this population with those in :arg:`new_data`.
        """
        # Redundant.
        self._items = list(new_data)

    def draw(self, key: Optional[R] = None, pos: Optional[int] = None) -> R:
        """Remove an item from the population.

        Identify an item either by value (in :arg:`key`) or by position
        (in :arg:`pos`). Remove that item from the collection, then return that item.

        Returns:
            The :class:`Individual` that is removed from the population

        Raises:
            :class:`TypeError`: If neither :arg:`key` nor :arg:`pos` is given.
        """
        if (key is None and pos is None):
            raise TypeError("An item must be specified, either by"
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
            #   Consider the trade-off.
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


class Population(AbstractCollection[D]):
    """A flat collection of individuals.
    """
    def __init__(self, *args: D):
        """
        Args:
            *args: Initial items in the population
        """
        super().__init__(*args)

    def copy(self) -> Self:
        """Return an independent population.

        Changes made to items in the new population should not affect
        items in this population. This behaviour depends on correct implementation
        of :meth:`.Individual.copy` in each item.

        Call :meth:`.Individual.copy` for each :class:`.Individual` in this
        population. Collect the results, then create a new population with
        these values.
        """
        return self.__class__(*[x.copy() for x in self._items])

    def sort(self: Self,
             ranker: Callable[[D], float] = lambda x: x.fitness) -> None:
        """Rearrange items by fitness, highest-first.

        Args:
            ranker: Sort key, called on each item prior to sorting.

        Effect:
            Rearrange items in this population.
        """
        self._items.sort(reverse=True, key=ranker)

    def reset_fitness(self: Self) -> None:
        """Remove fitness values of all Individuals in the population.

        Effect:
            For each item in this population, set
            its :attr:`.fitness Individual.fitness` to ``None``.
        """
        for x in self._items:
            x.reset_fitness()

    def best(self: Self) -> D:
        """Return the highest-fitness individual in this population.
        """
        best_individual: D = self[0]

        for x in self:
            if x.fitness > best_individual.fitness:
                best_individual = x

        return best_individual
