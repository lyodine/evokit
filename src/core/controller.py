""" The controller is an iterative optimizer that receives various evolutionary operators.
"""

# COMMENT: I strive to use typing where possible. This should enhance readability,
#   though the professor is the final judge of that.
# TODO: It is possible that using too many `typing` modules hinders understandability.
#   My experience is that surprisingly many in my cohord do not understand typing.
# NOTE: I try to only import objects that are used.
#   Per PEP 008, I will avoid name clashes. This should be easy
from typing import Callable
from typing import Self
from typing import Optional
from typing import TypeVar
from typing import Generic

# QUESTION: The Controller now exists in the same module as other abstract operators.
#   As a result, it must import from modules in the current repository.
#   If the Controller is moved to another module, then the exports may take the form of
#       `from core import Population, Genome, etc.`
#   This is arguably more elegent. However, moving Controller outside of core also means
#       we can no longer import it from `core`.

from .population import Population
from .population import Genome
from .population import GenomePool
# TODO: The GenomePool represents the population after parent selection - where parents are
#   grouped together, according to the input arity of the variator.
#   I wonder if there may be a better name for it. Maybe ParentPool?
from .evaluator import Evaluator
from .variator import Variator
from .selector import Selector
from .globals import report
from .globals import LogLevel

T = TypeVar("T", bound = Genome)

class Controller(Generic[T]):
    """The controller manages the learning process.
    """
    def __init__(self,
            population: Population[T],
            evaluator: Evaluator[T],
            parent_selector: Selector[T],
            variator: Variator[T],
            survivor_selector: Selector[T],
    ) -> None:
        """!Initialize an evolution controller with a set of configurable components.
            @param population: the initial population
            @param evaluator: The evaluator acts on an individual to determine its fitness.
            @param parent_selector: The parent selector applies to the population before variation. The range of the parent selector must match the domain of the variator.
            @param variator: The variator receives a collection of elements and outputs a list of genomes. These genomes are deposited into the population.
            @param survivor_selector: The parent selector that is applied before variation.
        """
        # Initialise with parameters
        self.population = population
        self.evaluator = evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.survivor_selector = survivor_selector
        # NOTE: Initialise the generation counter as 0
        # TODO: I decide to let "generation" represent the number of generations that have passed.
        #   For example, the counter starts as 0, then increments by one after the first generation.
        #   Is this choice okay?
        self.generation = 0


    # TODO: At this point, it is only possible to execute the controller
    #   A "truncator" module, I imagine, would keep executing the controller until a condition is met.
    #   The condition may be, for example, when an evaluator returns "truncate",
    #       when fitness reaches a certain level,
    #       or when too many generations have passed.
    #   With it, comes the problem of "how do I abstractly describe the truncation condition
    #       in a way that is extensible by the user?"
    def step(self) -> Self:
        """!Improve the population by one generation.
            @param accountant:  act on the population after the survivor selector
            @return: the population that results from the step
        """
        # Apply the parent selector
        initial_population: Population = len(self.population)

        # Evaluate the parent pool
        # TODO: This is a design decision.
        #   Here, calling `...evaluate_population` assigns a score to each genome  
        #       in the population.
        #   One alternative is to hand the evaluator to the selector.
        #   This is done so that the process is "flat" - otherwise, the controller
        #       would not have direct access to the evaluator.
        self.evaluator.evaluate_population(self.population)
        parents: GenomePool = self.parent_selector.select_to_pool(self.population)

        # Apply the child selector
        pop_before_variation = sum(len(x) for x in parents)
        children = self.variator.vary_pool(parents, None)

        # Apply the survivor selector
        pop_before_survivor_selection = len(children)

        self.evaluator.evaluate_population(children)
        survivors = self.survivor_selector.select_to_population(children)

        # The survivor become the next population.
        pop_after_survivor_selection = len(survivors)

        self.population = survivors
        self.evaluator.evaluate_population(self.population)
        self.population.sort()

        # NOTE: The following code account for error reporting purposes.
        #   This is to make it easier to understand what happens during the learning proces.
        #   I plan to move this funciton to a separate module, in reference to PyTorch's `profile`.
        report(LogLevel.DBG, f"Population progress: [{initial_population}]"
               f" -> (...)>PAR>({self.parent_selector.coarity})"
               f" -> [({self.parent_selector.coarity})~{pop_before_variation}]"
               f" -> ({self.variator.arity}) VAR ({self.variator.coarity})"
               f" -> [{pop_before_survivor_selection}] -> SUR"
               f" -> [{pop_after_survivor_selection}]"
               f", gen {self.generation}."
               f" Best score is now {self.population[0].score}")

        # NOTE: The following code code re-evaluates the best genome,
        #   then compares it with the "cached" score of the best genome.
        #   It reports an error if the scores do not match.
        #   This happens when the environment is stochastic... or some operator is badly implemented.
        #   I plan to move this function to a separate module.
        empirical_best_score = self.evaluator.evaluate(self.population[0])
        if self.population[0].score != empirical_best_score:
            report(LogLevel.WRN, f"Score inconsistent: cached {self.population[0].score}, actual {empirical_best_score}")

        # Self-explanatory: check if the size of the population follows the input / output arities of variators.
        #   I need to move it to another module.
        if pop_before_variation / self.variator.arity * self.variator.coarity != pop_before_survivor_selection:
            report(LogLevel.WRN, f"Variator arity inconsistent with population growth. "
                f"{pop_before_variation} / {self.variator.arity} * {self.variator.coarity} "
                f"= {int(pop_before_variation / self.variator.arity * self.variator.coarity)} <> {pop_before_survivor_selection}")

        report(LogLevel.INF, f"Best solution is: {str(self.population[0])}")

        self.generation = self.generation + 1
        # NOTE: Returning self allows chaining multiple calls to `step`
        return self