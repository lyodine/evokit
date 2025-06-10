from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar
from functools import wraps

from .accelerator.parallelisers import __getstate__
from .accelerator.parallelisers import __deepcopy__

from .accelerator import parallelise_task

from .population import Individual


from typing import Any

if TYPE_CHECKING:
    from typing import Self
    from typing import Type
    from typing import Callable
    from typing import Sequence
    from .population import Population
    from typing import Optional
    from concurrent.futures import ProcessPoolExecutor


D = TypeVar("D", bound=Individual[Any])


class _MetaEvaluator(ABCMeta):
    """Machinery.

    :meta private:

    Implement special behaviours in :class:`Evaluator`.
    """
    # ^^ Actually a private metaclass! :meta private: indeed.
    def __new__(mcls: Type[Any], name: str, bases: tuple[type],
                namespace: dict[str, Any]) -> Any:  # BAD
        ABCMeta.__init__(mcls, name, bases, namespace)
        # Remorseless metaclass abuse. Consider using __init_subclass__.
        # This bad boy violates so many OO practices. Everything for ease
        #   of use, I guess.

        def wrap_function(
                custom_evaluate: Callable[[Any, Any],
                                          tuple[float, ...]])\
                -> Callable[[Any, Any], tuple[float, ...]]:
            @wraps(custom_evaluate)
            def wrapper(self: Evaluator[Any], individual: Individual[Any],
                        *args: Any, **kwargs: Any) -> tuple[float, ...]:
                # If :attr:`retain_fitness` and the individual is scored, then
                #   return that score. Otherwise, evaluate the individual.
                if (self.retain_fitness and individual.has_fitness()):
                    return individual.fitness
                else:
                    return custom_evaluate(self, individual, *args, **kwargs)
            return wrapper

        namespace["evaluate"] = wrap_function(
            namespace.setdefault("evaluate", lambda: None)
        )
        return type.__new__(mcls, name, bases, namespace)


class Evaluator(ABC, Generic[D], metaclass=_MetaEvaluator):
    """Base class for all evaluators.

    Derive this class to create custom evaluators.

    Tutorial: :doc:`../guides/examples/onemax`.
    """
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Machinery.

        :meta private:

        Implement managed attributes.
        """
        instance = super().__new__(cls)
        instance.retain_fitness = False
        return instance

    def __init__(self: Self, *,
                 processes: Optional[int | ProcessPoolExecutor] = None,
                 share_self: bool = False) -> None:
        """
        See :class:`Variator` for parameters :arg:`processes`
        and :arg:`share_self`.
        """
        self.retain_fitness: bool
        """ If this evaluator should re-evaluate an :class:`Individual` whose
        :attr:`.fitness` is already set.
        """

        self.processes = processes

        self.share_self = share_self

    @abstractmethod
    def evaluate(self: Self, individual: D) -> tuple[float, ...]:
        """Evaluation strategy. Return the fitness of an individual.

        Subclasses should override this method.

        .. note::
            "Better" individuals should have higher fitness.

            :class:`.Selector` should prefer individuals with higher fitness.

        Args:
            individual: individual to evaluate
        """

    def evaluate_population(self: Self,
                            pop: Population[D]) -> None:
        """Context of :meth:`evaluate`.

        Iterate individuals in a population. For each individual, compute its
        fitness with :meth:`evaluate`, then assign that value to
        its :attr:`.Individual.fitness`.

        A subclass may override this method to implement behaviours that
        require access to the entire population.

        Effect:
            For each item in :arg:`pop`, set its :attr:`Individual.fitness`.

        .. note::
            This method must **never** return a value. It must assign to
            :attr:`.fitness` for each :class:`.Individual` in the
            :class:`.Population`.
        """
        fitnesses: Sequence[tuple[float, ...]] = parallelise_task(
            fn=type(self).evaluate,
            self=self,
            iterable=pop,
            processes=self.processes,
            share_self=self.share_self
        )

        for (individual, fitness) in zip(pop, fitnesses):
            individual.fitness = fitness

    __getstate__ = __getstate__
    __deepcopy__ = __deepcopy__
