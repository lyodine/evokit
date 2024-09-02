from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar
from functools import wraps
from typing import override
from typing import Any

from .population import Individual

if TYPE_CHECKING:
    from typing import Self
    from typing import Any
    from typing import Type
    from typing import Tuple
    from typing import Dict
    from typing import Callable
    from .population import Population

D = TypeVar("D", bound=Individual)


class MetaEvaluator(ABCMeta):
    """Machinery. Implement special behaviours in :class:`Evaluator`.

    :meta private:
    """
    # ^^ Actually a private metaclass! :meta private: indeed.
    def __new__(mcls: Type, name: str, bases: Tuple[type],
                namespace: Dict[str, Any]) -> Any:  # BAD
        ABCMeta.__init__(mcls, name, bases, namespace)
        # Remorseless metaclass abuse. Consider using __init_subclass__ instead.
        # This bad boy violates so many OO practices. Everything for ease
        #   of use, I guess.

        def wrap_function(custom_evaluate: Callable[[Any, Any], float]) -> Callable:
            @wraps(custom_evaluate)
            def wrapper(self: Evaluator, individual: Individual,
                        *args: Any, **kwargs: Any) -> float:
                if not isinstance(individual, Individual):
                    raise TypeError("The input is not an individual")
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


class Evaluator(ABC, Generic[D], metaclass=MetaEvaluator):
    """Base class for all evaluators.

    Derive this class to create custom evaluators.

    See :doc:`../guides/examples/onemax`.
    """
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Machinery. Implement managed attributes.

        :meta private:
        """
        instance = super().__new__(cls)
        instance.retain_fitness = False
        return instance

    def __init__(self: Self) -> None:
        self.retain_fitness: bool
        """ If this evaluator should re-evaluate an :class:`Individual` whose
        :attr:`.fitness` is already set.
        """

    @abstractmethod
    def evaluate(self: Self, individual: D) -> float:
        """Evaluation strategy. Return the fitness of an individual.

        Subclasses should override this method.

        Note:
            The implementation should assign higher fitness to better individuals.

        Args:
            individual: individual to evaluate
        """

    def evaluate_population(self: Self,
                            pop: Population[D]) -> None:
        """Context of :meth:`evaluate`.

        Iterate individuals in a population. For each individual, compute a
        fitness with :meth:`evaluate`, then assign that value to the individual.

        A subclass may override this method to implement behaviours that
        require access to the entire population.

        Note:
            This method must **never** return a value. It must assign to
            :attr:`.fitness` for each :class:`.Individual` in the
            :class:`.Population`. The result must be sorted, so that the earliest
            item has the highest fitness.
        """
        for x in pop:
            x.fitness = self.evaluate(x)
        pop.sort()

class NullEvaluator(Evaluator[Any]):
    @override
    def evaluate(self: Self, _: Any) -> float:
        return 0
