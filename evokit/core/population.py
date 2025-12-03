from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from typing import Callable
    from typing import Optional
    from typing import Self
    from typing import Type

from functools import wraps

from abc import ABC, abstractmethod, ABCMeta
from typing import Generic, TypeVar
from typing import Any

from collections import UserList as UserList
from typing import Sequence, Iterable

R = TypeVar('R')


class _MetaGenome(ABCMeta):
    """Machinery.

    :meta private:

    Implement special behaviours in :class:`Individual`.
    """
    def __new__(mcls: Type[Any], name: str, bases: tuple[type],
                namespace: dict[str, Any]) -> Any:  # `Any` is BAD
        ABCMeta.__init__(mcls, name, bases, namespace)

        def wrap_function(custom_copy:
                          Callable[[Individual[Any]], Individual[Any]])\
                -> Callable[[Individual[Any]], Individual[Any]]:
            @wraps(custom_copy)
            def wrapper(self: Individual[Any],
                        *args: Any, **kwargs: Any) -> Individual[Any]:
                custom_copy_result: Individual[Any]
                if self.has_fitness():
                    old_fitness = self.fitness
                    custom_copy_result = custom_copy(self, *args, **kwargs)
                    custom_copy_result.fitness = old_fitness
                else:
                    custom_copy_result = custom_copy(self, *args, **kwargs)

                custom_copy_result.parents = self.parents
                return custom_copy_result
            return wrapper

        namespace["copy"] = wrap_function(
            namespace.setdefault("copy", lambda: None)
        )
        return type.__new__(mcls, name, bases, namespace)


class Individual(ABC, Generic[R], metaclass=_MetaGenome):
    """Base class for all individuals.

    Derive this class to create custom representations.

    The individual stores the encoding (:attr:`.genome`)
    and fitness (:attr:`.fitness`) of a representation.

    The individual can information outside of the genotype, such as a
        `.fitness`, a reference to the parent, and strategy parameter(s).

    .. note::
        Implementation should store the genotype in :attr:`.genome`.

    Tutorial: :doc:`../guides/examples/onemax`.
    """
    def __new__(cls: Type[Self], *args: Any, **kwargs: Any) -> Self:
        """Machinery.

        :meta private:

        Implement managed attributes.
        """
        instance: Self = super().__new__(cls)
        instance._fitness = None
        instance.parents = None
        return instance

    @abstractmethod
    def __init__(self: Self,) -> None:
        self._fitness: Optional[tuple[float, ...]]

        #: Parents of the individual, registered with :meth:`inherit`.
        self.parents: Optional[tuple[Self, ...]]

        #: Genotype of the individual.
        self.genome: R

    @property
    def fitness(self: Self) -> tuple[float, ...]:
        """Fitness of an individual.

        Writing to this property changes the fitness of the individual.
        If this individual has yet to be assigned a fitness, reading
        from this property raises an exception.

        To determine if the individual has a fitness, call
        :meth:`has_fitness`.

        Return:
            Fitness of the individual

        Warning:
            If the current fitness is ``None``, return ``(nan,)``.
            This may happen when, for example, an offspring
            has just been produced.
        """

        if (self._fitness is None):
            return (float('nan'),)
        else:
            return self._fitness

    @fitness.setter
    def fitness(self: Self, value: tuple[float, ...]) -> None:
        """Sphinx does not pick up docstrings on setters.

        This docstring should never be seen.

        Arg:
            Whatever.
        """
        self._fitness = value

    def reset_fitness(self) -> None:
        """Reset the fitness of the individual.

        Effect:
            The :attr:`.fitness` of this individual becomes ``None``.
        """
        self._fitness = None

    def has_fitness(self) -> bool:
        """Return `True` if :attr:`.fitness` is not None.
            Otherwise, return `False`.
        """
        return self._fitness is not None

    @abstractmethod
    def copy(self) -> Self:
        """Return an identical copy of the individual.

        Subclasses should override this method.

        Operations on in this individual should not affect the new individual.
        In addition to duplicating :attr:`.genome`, the implementation should
        decide whether to retain other fields such as :attr:`.fitness`.

        .. note::
            Ensure that changes made to the returned value do not affect
            the original value.

            The :attr:`.parents` attribute is copied on automatically.
        """

    def set_parent(self: Self,
                   parent: tuple[Self, ...],
                   max_parents: int):
        """Register :arg:`parent` as the parent to :arg:`self`.

        Also unlink the :arg:`max_parents`\\ :sup:`th`
        :attr:`.Individual.parent`,
        if one exists, of this individual. Consequently, the parent
        of an individual is unlinked if that individual ever becomes
        first in a long chain of parents.

        This approach is not perfect, but does well to save memory.
        The alternative is to preserve the parent of an individual
        if it is part of a _short_ chain of parents.
        """
        # I have considered an alternative approach of
        #   maintaining a deque of parents.
        # This is a horrible idea. Making a deque for each
        #   individual is incredibly costly.
        self.parents = parent

        _disinherit_me: tuple[Self, ...] = (self,)
        for _ in range(max_parents):
            # A monster of a comprehension.
            _disinherit_me = tuple(
                (x for _pelops in _disinherit_me
                 if _pelops.parents is not None
                 for x in _pelops.parents))

        if _disinherit_me is not None:
            for _iphigenia in _disinherit_me:
                _iphigenia.parents = None


D = TypeVar("D", bound=Individual[Any])


class Population(UserList[D], Generic[D]):
    """A flat collection of individuals.
    """
    def __init__(self: Self,
                 initlist: Optional[Sequence[D]] | Iterable[D] = None):
        """
        Args:
            args: Initial items in the population
        """
        super().__init__(initlist)

    def copy(self) -> Self:
        """Return an independent population.

        Changes made to items in the new population should not affect
        items in this population. This behaviour depends on correct
        implementation of :meth:`.Individual.copy` in each item.

        Call :meth:`.Individual.copy` for each :class:`.Individual` in this
        population. Collect the results, then create a new population with
        these values.
        """
        return self.__class__([x.copy() for x in self])

    def reset_fitness(self: Self) -> None:
        """Remove fitness values of all Individuals in the population.

        Effect:
            For each item in this population, set
            its :attr:`.fitness Individual.fitness` to ``None``.
        """
        for x in self:
            x.reset_fitness()

    def best(self: Self) -> D:
        """Return the highest-fitness individual in this population.
        """
        best_individual: D = self[0]
        # from evokit.core.population import Population
        # a = Population(1, 2, 3)
        # b = Population("1", "2", "3")

        for x in self:
            if best_individual.fitness == (float('nan'),):
                best_individual = x
            elif x.fitness == (float('nan'),):
                pass
            elif x.fitness > best_individual.fitness:
                best_individual = x

        return best_individual

    def __str__(self: Self) -> str:
        return "[" + ", ".join(str(item) for item in self) + "]"

    __repr__ = __str__

    # @override
    # def __add__(self: Self, other: Iterable[D]) -> Population[D]:
    #     return Population[D](*self, *other)

    # @override
    # def __add__(self: Self, other: Population[D]) -> Population[D]:
    #     best_individual: D = self[0]

    #     for x in self:
    #         if best_individual.fitness == (float('nan'),):
    #             best_individual = x
    #         elif x.fitness == (float('nan'),):
    #             pass
    #         elif x.fitness > best_individual.fitness:
    #             best_individual = x

    #     return best_individual

    # def __str__(self: Self) -> str:
    #     return "[" + ", ".join(str(item) for item in self) + "]"

    # @overload
    # def __getitem__(self: Self, index: int) -> D:
    #     pass

    # @overload
    # def __getitem__(self: Self, index: slice) -> Population[D]:
    #     pass

    # @override
    # def __getitem__(self: Self, index: int | slice) -> D | Population[D]:
    #     if isinstance(index, int):
    #         return self._items[index]
    #     else:
    #         return Population[D](*self._items[index])

    # @overload
    # def __setitem__(self: Self,
    #                 index: int,
    #                 value: D) -> None:
    #     pass

    # @overload
    # def __setitem__(self: Self,
    #                 index: slice,
    #                 value: Population[D]) -> None:
    #     pass

    # @override
    # def __setitem__(self: Self, index: int | slice,
    #                 value: D | Population[D]) -> None:
    #     if isinstance(index, int):
    #         assert not isinstance(value, Population)
    #         self._items[index] = value
    #     else:
    #         assert isinstance(value, Population)
    #         self._items[index] = value

    # def __delitem__
    # def __lenitem__
    # def insert

    # def append(self, value: R) -> None:
    #     """Append an item to this collection.

    #     Args:
    #         value: The item to add to this item
    #     """
    #     # TODO value is a really bad name
    #     self._items.append(value)

    # def join(self, values: Iterable[R]) -> Self:
    #     """Produce a new collection with items from :arg:`self` and
    #     :arg:`values`.

    #     Args:
    #         values: Collection whose values are appended to this collection.
    #     """
    #     # TODO Inefficient list comprehension. Looks awesome though.
    #     # Improve at my own convenience.
    #     return self.__class__(*self, *values)

    # def populate(self, new_data: Iterable[R]) -> None:
    #     """Replace items in this population with items in :arg:`new_data`.

    #     Args:
    #         new_data: Collection whose items replace items in this
    #             population.

    #     Effect:
    #         Replace all items in this population with those in
    # :arg:`new_data`.
    #     """
    #     # Redundant.
    #     self._items = list(new_data)

    # def draw(self, key: Optional[R] = None, pos: Optional[int] = None) -> R:
    #     """Remove an item from the population.

    #     Identify an item either by value (in :arg:`key`) or by position
    #     (in :arg:`pos`). Remove that item from the collection,
    #     then return that item.

    #     Returns:
    #         The :class:`Individual` that is removed from the population

    #     Raises:
    #         :class:`TypeError`: If neither :arg:`key` nor :arg:`pos` is
    # given.
    #     """
    #     if (key is None and pos is None):
    #         raise TypeError("An item must be specified, either by"
    #                         " value or by position. Neither is given.")
    #     elif (key is not None and pos is not None):
    #         raise TypeError("The item can only be specified by value"
    #                         "or by position. Both are given.")
    #     elif (pos is not None):
    #         a: R = self[pos]
    #         del self[pos]
    #         return a
    #     elif (key is not None):
    #         has_removed = False
    #         # TODO refactor with enumerate and filter.
    #         #   Still up for debate. Loops are easy to understand.
    #         #   Consider the trade-off.
    #         for i in range(len(self)):
    #             # Development mark: delete the exception when I finish this
    #             if self[i] == key:
    #                 has_removed = True
    #                 del self[i]
    #                 break

    #         if (not has_removed):
    #             raise IndexError("the requested item is not in the list")
    #         else:
    #             return key
    #     else:
    #         raise RuntimeError("key and pos changed during evaluation")
