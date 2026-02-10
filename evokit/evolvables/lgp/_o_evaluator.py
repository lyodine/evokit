from ...core import Evaluator
from ._o_individual import LinearGeneticProgram
from ._program import RegisterStates
from ._optimise import optimise_and_mask, optimise_and_reduce
from typing import Self, Optional, TYPE_CHECKING, Sequence, Callable, Literal
from typing import override
if TYPE_CHECKING:
    from concurrent.futures import ProcessPoolExecutor
    from ._program import Instruction

#: A fitness case is a tuple of form
#: `((input_registers, input_constants), outputs)`,
#: where `input_registers`, `input_constants`, and
#: are all tuples.
type FitnessCase[T] = tuple[tuple[tuple[T, ...],
                                  tuple[T, ...]],
                            tuple[T, ...]]


class LGPEvaluator[T](Evaluator[LinearGeneticProgram[T]]):
    def __init__(self: Self,
                 fitness_cases: Sequence[FitnessCase],
                 output_indices: set[int],
                 optimise_mode: Literal["none", "mask", "reduce"],
                 fitness_function: Callable[[Sequence[T],
                                             Sequence[T]], float],
                 verbose=False,
                 processes: "Optional[int | ProcessPoolExecutor]" = None,
                 share_self: bool = False) -> None:
        """
        Args:
            processes: See :class:`.Variator`.
            share_self: See :class:`.Variator`.
        """
        super().__init__(processes=processes,
                         share_self=share_self)
        self.evaluation_context = RegisterStates(
            # Because registers and constants are
            #   reset each run.
            constants=None,  # type: ignore
            registers=None,  # type: ignore
            verbose=verbose
        )
        # WHY IS VERBOSE GIVEN IN TWO PLACES?
        self.verbose = verbose

        self.fitness_cases = fitness_cases

        self.output_indices = output_indices

        # self.optimiser: ???
        if optimise_mode == "none":
            self.optimiser = None
        elif optimise_mode == "mask":
            self.optimiser = optimise_and_mask
        else:
            self.optimiser = optimise_and_reduce

        self.fitness_function = fitness_function

    @override
    def evaluate(self: Self,
                 individual: LinearGeneticProgram[T]) -> tuple[float, ...]:
        """This class overrides `evaluate_population` instead.
        """
        accumulated_fitness: float = 0

        code_to_run: Sequence[Instruction[T] | None]
        if self.optimiser is not None:
            code_to_run = self.optimiser(individual.genome,
                                         self.output_indices)
        else:
            code_to_run = individual.genome

        for ((input_registers, input_constants), outputs)\
                in self.fitness_cases:
            self.evaluation_context.registers = list(input_registers)
            self.evaluation_context.constants = input_constants
            self.evaluation_context.run(instructions=code_to_run)

            actual_outputs = [self.evaluation_context.registers[i]
                              for i in range(
                                  len(self.evaluation_context.registers))
                              if i in self.output_indices]
            accumulated_fitness += self.fitness_function(outputs,
                                                         actual_outputs)

        return (accumulated_fitness,)
