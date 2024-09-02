from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from .population import Individual

if TYPE_CHECKING:
    from typing import Self

    from .population import Population

T = TypeVar("T", bound=Individual)

class _MetaEvaluator(ABCMeta):
    """Machineary for the evaluator.
        Because ABC (abstract base class) is also implemented with metaclasses,
            and a class cannot have two metaclasses, I must implement the following:
            (1) MetaEvaluator extends ABCMeta
            (2) Evaluator has MetaEvaluator as metaclass, thereby indirectly
                using ABCMeta as metaclass
            (3) Evaluator extends abc.ABC, which has ABCMeta as metaclass.
            (4) Things work out, because both "chains" lead to the same
                metaclass, which is ABCMeta.

        ABCMeta <|-- MetaEvaluator
        ^               ^
        | <metaclass>   | <metaclass>
        |               |
        abc.ABC <|-- Evaluator

    """
    # cls, name, bases, attrs
    def __new__(mcls, name, bases, namespace):
        """
        """
        # Moderately cursed Python magic.
        # This metaclass modifies the behaviour of a evaluator.
        def wrap_function(custom_evaluate):
            def wrapper(*args, **kwargs) -> float:
                individual = args[1]
                if not isinstance(individual, Individual):
                    raise TypeError("Evaluator is not an individual")
                elif individual.is_scored():
                    return individual.score
                else:
                    score: float = custom_evaluate(*args, **kwargs)
                    individual.score = score
                    return score
            return wrapper

        if name != "Evaluator":
            namespace["evaluate"] = wrap_function(
                namespace.setdefault("evaluate", lambda: None)
            )
        # This is necessary. Because __new__ is an instance method.
        return type.__new__(mcls, name, bases, namespace)

class Evaluator(ABC, Generic[T]):
    """Base class for all evaluators.

    Derive this class to create custom evaluators.
    """
    @staticmethod
    def evaluate_shortcut(func):
        """Annotation that applies the "evaluator guard" to an evaluator.

        A child class may apply this annotation to `evaluate`. Doing so
        prevents the evaluator from re-scoring individuals
        that already have a fitness.
        
        This may accelerate learning, as individuals retained from the
        parent generation are no longer re-evaluated. However,
        doing so also prevents the evaluator from correctly modeling
        a changing fitness landscape, where the fitness of an
        individual may change across generations.
        """
        def wrapper(*args, **kwargs) -> float:
            print ("shortcut used")
            individual = args[1]
            if not isinstance(individual, Individual):
                raise TypeError("Evaluator is not an individual")
            elif individual.is_scored():
                return individual.score
            else:
                score: float = func(*args, **kwargs)
                individual.score = score
                return score
        return wrapper

    @abstractmethod
    def evaluate(self: Self, individual: T)-> float:
        """Evaluation strategy of the evaluator.
        
        All subclasses should override this method. The implementation should
        assign higher fitness to higher-quality individuals.

        Args:
            individual: individual to evaluate

        Return:
            Fitness of the individual
        """

    def evaluate_population(self: Self,
                            pop: Population[T])-> Population[T]:
        """Context for the evaluation strategy.
        
        Iterate individuals in a population. For each individual, assign to it a
            fitness given by `evaluate`.
        """
        for x in pop:
            x.score = self.evaluate(x)
        return pop






