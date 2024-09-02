from typing import Self
from typing import TypeVar
from typing import Generic

import abc
from .population import Population
from .population import Genome

T = TypeVar("T", bound=Genome)

# NOTE: From a Java background, I am used to creating a exception type for each exceptional case that may arise.
class ScoringException(Exception):
    """This exception arises from exceptions thrown during the scoring process.
        TODO: The only place that raises this exception, as of 2024-04-05, is
            when the thing that is being scored is not a genome.
        Solution: try to create a exception class that matches
            "operator type mismatch"
    """


class Evaluator(abc.ABC, Generic[T]):
    """The evaluator evaluates the fitness of a Genome.
    """
    @staticmethod
    def evaluate_shortcut(func):
        """!Apply the "dynamic scoring" heuristic to the evaluate(.) method.
        """

        def wrapper(*args, **kwargs) -> float:
            genome = args[1]
            if not isinstance(genome, Genome):
                raise ScoringException("This thing is not a genome!")
            elif genome.is_scored():
                return genome.score
            else:
                score: float = func(*args, **kwargs)
                genome.score = score
                return score
        return wrapper


    @abc.abstractmethod
    @evaluate_shortcut
    def evaluate(self: Self, s1: T)-> float:
        """!Evaluate an individual and return the score.
            Higher scores are better.
        """


    # TODO not implemented. Should I let the evaluator directly report truncation? If so,
    #   then this method belongs here; otherwise, remote it completely, and move
    #   the reporting mechanism to the genome (as a field)
    # @abc.abstractmethod
    # def truncate(self: Self) -> bool:
    #     """Return if a termination condition has been reached.
    #     """
    #     return False
    def evaluate_population(self: Self, pop: Population[T])-> Population[T]:
        """!Score every individual of a population
        """
        for x in pop:
            x.score = self.evaluate(x)
        return pop






