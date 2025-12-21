from __future__ import annotations

from typing import TYPE_CHECKING

from .accelerator import parallelise_task

from .accelerator.parallelisers import __getstate__
from .accelerator.parallelisers import __deepcopy__

if TYPE_CHECKING:
    from typing import Optional
    from typing import Sequence
    from typing import Self
    from typing import Type
    from concurrent.futures import ProcessPoolExecutor

from logging import warning
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

        instance.arity = None
        instance.processes = None
        instance.share_self = False

        return instance

    def __init__(self: Self,
                 *args: Any,
                 processes: Optional[int | ProcessPoolExecutor] = None,
                 share_self: bool = False,
                 **kwargs: Any) -> None:
        """
        See :class:`Variator` for parameters :arg:`processes`
        and :arg:`share_self`.
        """

        #: Size of input to :meth:`vary`
        self.arity: Optional[int]

        #: Multiprocessing capabilities. See :meth:`__init__`.
        self.processes = processes

        """If attributes of this object will be shared when
        multiprocessing. See :meth:`__init__`.
        """
        self.share_self = share_self

    @abstractmethod
    def vary(self: Self,
             parents: Sequence[D],
             *args: Any,
             **kwargs: Any) -> tuple[D, ...]:
        """Apply the variator to a tuple of parents

        Produce a tuple of individuals from a sequence of individuals.

        The length of :arg:`.parents` is at most :attr:`.arity`.
        """
        pass

    def _group_to_parents(self: Self,
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
                        population: Population[D],
                        *args: Any,
                        **kwargs: Any) -> Population[D]:
        """Vary the population.

        The default implementation separates ``population`` into groups
        of size `.arity`, call `.vary` with each group as argument,
        then collect and returns the result.

        Args:
            population: Population to vary.

        .. note::
            The default implementation calls :meth:`.Individual.reset_fitness`
            on each offspring to clear its fitness. Any implementation that
            overrides this method should do the same.
        """
        parent_groups: Sequence[Sequence[D]] =\
            self._group_to_parents(population)

        if len(parent_groups) == 0:
            warning(f"Cannot procreate. Population has"
                    f" {len(population)} individuals,"
                    f" grouped into {len(parent_groups)}"
                    f" sets of parents (each has size {self.arity})."
                    f" Too few to procreate.")

        processes = self.processes
        share_self = self.share_self
        nested_results: Sequence[tuple[D, ...]] =\
            parallelise_task(fn=self.vary.__func__,  # type: ignore
                             self=self,
                             iterable=parent_groups,
                             processes=processes,
                             share_self=share_self)

        for group in nested_results:
            for individual in group:
                individual.reset_fitness()

        next_population = Population(list(sum(nested_results, ())))

        return next_population

    __getstate__ = __getstate__
    __deepcopy__ = __deepcopy__


class NullVariator(Variator[D]):
    """Variator that does not change anything
    """
    def __init__(self: Self) -> None:
        self.arity = 1

    @override
    def vary(self: Self, parents: Sequence[D]) -> tuple[D, ...]:
        return tuple(parents)
