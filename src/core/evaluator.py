from typing import Self
from typing import TypeVar
from typing import Generic

from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from .population import Population
from .population import Genome

T = TypeVar("T", bound=Genome)



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
        """!Python magic. This is only moderately cursed: one gets used to
            metaclasses after a while.
            This {decorator/metaclass} modifies the behaviour of a evaluator.
        """
        def wrap_function(custom_evaluate):
            def wrapper(*args, **kwargs) -> float:
                genome = args[1]
                if not isinstance(genome, Genome):
                    raise TypeError("Evaluator is not a genome")
                elif genome.is_scored():
                    print("no shortcut!")
                    return genome.score
                else:
                    print("shortcut!")
                    score: float = custom_evaluate(*args, **kwargs)
                    genome.score = score
                    return score
            return wrapper
        
        if name != "Evaluator":
            namespace["evaluate"] = wrap_function(
                namespace.setdefault("evaluate", lambda: None)
            )
        # This is necessary. Because __new__ is 
        return type.__new__(mcls, name, bases, namespace)

class Evaluator(ABC, Generic[T]):
    """The evaluator evaluates the fitness of a Genome.
    """
    @staticmethod
    def evaluate_shortcut(func):
        """!Apply the "dynamic scoring" heuristic to the evaluate(.) method.
        """
        def wrapper(*args, **kwargs) -> float:
            print ("shortcut used")
            genome = args[1]
            if not isinstance(genome, Genome):
                raise TypeError("Evaluator is not a genome")
            elif genome.is_scored():
                return genome.score
            else:
                score: float = func(*args, **kwargs)
                genome.score = score
                return score
        return wrapper

    @abstractmethod
    def evaluate(self: Self, s1: T)-> float:
        """!Evaluate an individual and return the score.
            Higher scores are better.
        """

    def evaluate_population(self: Self,
                            pop: Population[T])-> Population[T]:
        """!Iterate through genomes in a population. For each genome,
            assign to it a fitness.
        """
        for x in pop:
            x.score = self.evaluate(x)
        return pop






