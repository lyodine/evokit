from ..lgp._optimise import optimise_and_mask, optimise_and_reduce
from ..lgp._program import CellSpecifier
from ..lgp._program import Condition
from ..lgp._program import Instruction
from ..lgp._program import Label
from ..lgp._program import Operation
from ..lgp._program import StateVectorType
from ..lgp._program import StructureScope
from ..lgp._program import _operation_to_text
from typing import Optional

from typing import Literal, Self, Sequence


class RegisterStates[R]:
    """Context for executing linear programs.

    A context stores states of a program. These states
    include constant and variable registers. Call methods
    of the context to run instructions in this state.

    This context is generic, and as such works with
    all endofunctions in its type argument [#]_.

    .. [#] Yes, you read that right. *Numbers*
        are so vanilla. Want to evolve programs
        in functions? Graphs? INI files?
        What about makeup tutorials? Yes to all
        the above. EvoKit got you back.
    """
    def __init__(self: Self,
                 registers: list[R],
                 constants: tuple[R, ...],
                 verbose: bool = False):
        """
        Args:
            registers: Variable registers, registers for short.
            constants: Constant registers. Someone once called
                these constants and I wholeheartedly agree with that.
            verbose: If ``True``, then evaluating each operation or
                condition also prints to STDOUT.
        """
        #: The register vector stores mutable state variables.
        #: Set with :meth:`.set_register`.
        self.registers: list[R]
        self.set_registers(registers)

        #: The constant vector stores immutable state variables.
        #: Set with :meth:`.set_constants`.
        self.constants: tuple[R, ...]
        self.set_constants(constants)

        #: If ``True``, then each operation also
        #: prints what it does.
        self.verbose = verbose

    def set_registers(self: Self, registers: list[R]) -> None:
        """Set the register vector to :arg:`registers`.
        """
        self.registers = registers

    def set_constants(self: Self, constants: tuple[R, ...]) -> None:
        """Set the constant vector to :arg:`constants`.
        """
        self.constants = constants

    def get_cell_value(self: Self,
                       spec: CellSpecifier) -> R:
        """Return the value in the cell specified by
        :arg:`spec`.
        """
        return self.get_state_vector(
            spec[0])[spec[1]]

    def get_state_vector(self: Self,
                         celltype: StateVectorType)\
            -> Sequence[R]:
        """Return the state vector specified by :arg:`celltype`.
        """
        match celltype:
            case StateVectorType.register:
                return self.registers
            case StateVectorType.constant:
                return self.constants

    def run_optimised(self: Self,
                      instructions: Sequence[Instruction],
                      output_indices: set[int],
                      remove_introns: bool) -> None:
        """Attempt to optimise, then execute :arg:`instructions`
        in this context.

        See :meth:`.index_introns` for the optimisation algorithm.

        Args:
            instructions: See :meth:`.run`
            output_indices: Indices of variable registers that
                will be used as output. Instructions that
                do not affect these registers will be marked
                as introns.
            remove_introns: If ``True``, then remove (instead
                of replacing with None) introns. This costs
                significantly more, but will shorten the
                instruction sequence.
        """

        optimiser = optimise_and_reduce if remove_introns\
            else optimise_and_mask

        self.run(optimiser(instructions,
                           output_indices))

    def run(self: Self,
            instructions: Sequence[Optional[Instruction]]) -> None:
        """Execute :arg:`instructions` in this context.

        Args:
            instructions: A sequence of instructions to run.
                Items that are ``None`` are skipped.

        Effect:
            Executing an :class:`Operation` updates
            :attr:`.registers`.
        """
        # Replace introns with None. The interpreter will not
        #   execute instructions that are None.
        # `None` should take up less space than the replaced
        #   instruction. Will this improve performance?
        # This approach is preferable than passing a set of indices to
        #   skip because structures run code in their mini contexts,
        #   where the same instructions may have a different index.
        current_line: int = 0

        while current_line < len(instructions):
            lines_skipped = self._run_instruction(instructions,
                                                  current_line)
            current_line += lines_skipped

    def check_condition(self: Self, cond: Condition) -> bool:
        """Execute a condition in the current context, return the result.
        """
        # Behold, Pythonic code!
        # TODO rewrite logic
        result: bool = cond.function(*(self.get_cell_value(spec)
                                       for spec in cond.args))
        if self.verbose:
            print(f"?? {_operation_to_text(cond.function,
                                           cond.args)} -> {result}")

        return result

    def _run_instruction(self: Self,
                         instructions: Sequence[Optional[Instruction]],
                         pos: int) -> int:
        """Execute an instruction.

        Execute the :arg:`pos`\\ :sup:`th` instruction
        in :arg:`instructions`.

        Return the number of lines advanced as a result.
        Running a single operation advances the execution
        pointer by 1; running control structures may
        skip more lines.

        Args:
            instructions: A sequence of instructions. This is the
                actual executable program.

            pos: Position of current execution pointer.

        """
        instruction: Optional[Instruction] = instructions[pos]
        match instruction:
            case Operation():
                return self._run_operation(instruction)
            case StructureScope():
                return self._run_structure_scope(instruction,
                                                 instructions,
                                                 pos)
            case Label():
                return self._run_label(instruction)
            case None:
                return 1
            case _:
                raise ValueError("Instruction type"
                                 f" {type(instruction).__name__}"
                                 " not recognised.")

    def _run_label(self: Self, instruction: Label) -> Literal[1]:
        """Execute a label, which does nothing.

        Return the number of lines executed (always 1).
        """
        if self.verbose:
            print(f"{instruction.text}: (label)")
        return 1

    def _run_operation(self: Self,
                       instruction: Operation) -> Literal[1]:
        """Execute :arg:`instruction` in this context.

        Return the number of lines executed  (always 1).
        """
        if instruction.target < 0:
            raise ValueError("Malformed instruction: assignment to"
                             f" index {instruction.target}.")
        else:
            self.registers[instruction.target] =\
                instruction.function(
                    *(self.get_cell_value(s)
                      for s in instruction.operands))
            if self.verbose:
                print(_operation_to_text(instruction.function,
                                         instruction.operands,
                                         instruction.target,))
        return 1

    def _run_structure_scope(self: Self,
                             instruction: StructureScope,
                             instructions: Sequence[Optional[Instruction]],
                             pos: int) -> int:
        """Execute a control structure.

        Use `.StructureScope.scope` to find the scope
        of the structure, then run all instructions within
        the scope.
        """
        scope: int = instruction.scope(
            instructions,
            pos)

        instructions_to_run: Sequence[Optional[Instruction]] =\
            instructions[pos + 1:pos + scope + 1]

        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  f" over next {scope} lines.")

        instruction.stype(self,
                          instructions_to_run)
        return scope + 1  # +1 to include the structure instruction itself

    def _print_instructions(self: Self,
                            instructions:
                            Sequence[Optional[Instruction]]) -> None:
        for instruction in instructions:
            print(f"> {instruction}")

    def __str__(self: Self) -> str:
        return (f"LGP execution context here. Register states:\n"
                f"> {self._get_register_states()}")

    def _get_register_states(self: Self) -> str:
        return f"r{str(self.registers)}, c{str(self.constants)}"

    __repr__ = __str__

    def copy(self: Self) -> Self:
        return type(self)(self.registers.copy(),
                          self.constants,
                          self.verbose)
