from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from typing import Annotated
from typing import Any
from typing import Sequence
from typing import Literal
from typing import Optional
from typing import Concatenate
from typing import Self, override
from typing import Iterable
from typing import Callable

from typing import TypeAlias
from enum import Enum, auto

from .._utils.dependency import ensure_installed

ensure_installed("numpy")


class Instruction[R]():
    """Base class for all instructions.

    An instruction is a "line" in the program.
    """
    ...


class StructureType(ABC):
    """Base class for all control structure types.

    The type of a control structure decides how many times
    its body is executed: whether once (:class:`.If`),
    for a number of times (:class:`.For`), or until an
    expression evaluates to ``True`` (:class:`.While`).

    Derive this class to create custom structure types.
    """
    @abstractmethod
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        """Invoke instructions in a stateful context.

        Args:
            lgp: That context.
            instructions: Instructions to execute.
        """


class StructureScope(ABC, Instruction):
    """Base class for all control structure scopes.

    The scope of a control structure decides how many
    lines following it become part of its body.
    The scope also contains a :class:`.StructureScope`,
    which decides how many times this body is executed.

    Derive this class to create custom scopes.
    """
    @abstractmethod
    def __init__(self: Self,
                 stype: StructureType,
                 *args: Any,
                 **kwargs: Any) -> None:
        """
        Args:
            stype: Type of the control structure.
        """


class StructOverLines(StructureScope):
    """Control structure that spans a number of lines.
    """
    def __init__(self: Self, stype: StructureType, line_count: int) -> None:
        """
        Args:
            stype: Type of the control structure.
            line_count: Number of lines that the control structure spans.
        """
        self.stype: StructureType = stype
        self.line_count: int = line_count


class StructUntilLabel(StructureScope):
    """Control structure that extends to the given label.
    """
    def __init__(self: Self, stype: StructureType, label: str):
        """
        Args:
            stype: Type of the control structure.
            label: Text of label that terminates this control structure.
        """
        self.stype: StructureType = stype
        self.label: str = label


class StructNextLine(StructureScope):
    """Control structure that spans one line.
    """
    def __init__(self: Self, stype: StructureType):
        """
        Args:
            stype: Type of the control structure.
        """
        self.stype: StructureType = stype


class Label():
    """Text label.

    Use with :class:`StructUntilLabel`.
    """
    def __init__(self: Self, text: str):
        """
        Args:
            label: Text of the label.
        """
        self.text = text


class For(StructureType):
    """"For" loop.

    A control structure with this type repeats its body for
    :attr:`.count` times. Not really a for loop, since it does
    not use a condition.
    """
    def __init__(self: Self, count: int):
        #: Number of times the body executes for.
        self.count = count

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        for _ in range(self.count):
            lgp.run(instructions)


class While(StructureType):
    """While loop.

    A control structure with this type repeats its body
    until :attr:`.condition` evaluates to ``True`` or
    :attr:`.loop_cap` loops have elapsed.

    .. info::

        To prevent infinite execution, this structure
        is a glorified *for* loop.
    """

    #: Maximum number of iterations a :class:`While` loop can run for.
    loop_cap = 20

    def __init__(self: Self, condition: Condition):
        """
        Args:
            condition: Condition that, if satisfied, ends the structures.
        """
        #: Condition that must be satisfied for the structure to stop.
        self.condition = condition

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        for _ in range(While.loop_cap):
            if (lgp.check_condition(self.condition)):
                lgp.run(instructions)
            else:
                break


class If(StructureType):
    """Structure with condition execution.

    A control structure with this type executes
    once if :arg:`condition` evaluates to ``True``.
    Otherwise, the structure is skipped and does nothing.
    """
    def __init__(self: Self, condition: Condition):
        self.condition = condition

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        if (lgp.check_condition(self.condition)):
            lgp.run(instructions)


@dataclass
class ValueRange:
    min: float
    max: float


class StateVectorType(Enum):
    """Type of a state vector.

    A linear program stores two state vectors.
    Here, :attr:`.LinearProgram.registers` are mutable;
    :attr:`.LinearProgram.constants` are immutable.
    """
    register = auto()
    constant = auto()


#: Tuple that locates an item in a state vector.
#: The first item (a :class:`StateVectorType`) specifies the
#: vector; the second item (an :class:`int`) gives the index.
CellSpecifier: TypeAlias = tuple[StateVectorType,
                                 Annotated[int, ValueRange(0,
                                                           float('inf'))]]


def name_cell_specifier(spec: CellSpecifier) -> str:
    """Map a :class:`.CellSpecifier` to a name:
    *. Cells in a variable register become ``r[i]``.
    *. Cells in a constant register become ``c[i]``.
    """
    if spec[0] == StateVectorType.register:
        return f"r[{spec[1]}]"
    else:
        return f"c[{spec[1]}]"


def cell(pos: int) -> CellSpecifier:
    """Convenience function for creating a
    :class:`.CellSpecifier`.

    Arg:
        pos: If :arg:`pos>=0`, specify the :arg:`pos`\\ :sup:`th`
            register. Otherwise, specify the :arg:`abs(pos)-1`
            :sup:`th` constant.
    """
    if pos >= 0:
        return (StateVectorType.register, pos)
    else:
        return (StateVectorType.constant, abs(pos) - 1)


def cells(*poses: int) -> tuple[CellSpecifier, ...]:
    """Convenience function for creating a
    tuple of :class:`.CellSpecifier`\\ s.

    Arg:
        poses: See :meth:`.cell`.
    """
    return tuple(cell(p) for p in poses)


@staticmethod
def _operation_to_text(function: Callable,
                       operands: Sequence[CellSpecifier],
                       target: Optional[int] = None) -> str:
    """Return the string representation of an operation
    """
    operands_str: list[str] = [
        name_cell_specifier(spec) for spec in operands
    ]
    return (f'r[{target}] := ' if target is not None else "")\
        + f'{function.__name__}({", ".join(operands_str)})'


#: Type for an endofunction.
type Endofunction[R] = Callable[Concatenate[R, ...], R]
# Technically this type means functions that take
#   one R as argument as minimum -- it doesn't care what
#   arguments come next.
# This is because to my knowledge, Python has no facility
#   for this -- typing it variadic would preclude,
#   for example, functions such ``add(a, b)`` that
#   are not variadic. Some features are "left to future PEPs";
#   I suspect what I want is among those.


@dataclass
class Operation[R](Instruction[R]):
    """An operation.

    Executing this operation calls :arg:`function`
    with :attr:`.operands` as arguments. The result
    should then be deposited into the :attr:`.target`\\ s
    variable register.
    """
    def __init__(self: Self,
                 function: Endofunction[R],
                 target: int,
                 operands: tuple[CellSpecifier, ...]):
        """
        Args:
            function: A function.
            target: A position in the variable register.
            operands: Arguments to :arg:`function`.
        """
        self.function: Endofunction[R] = function
        self.target: int = target
        self.operands: tuple[CellSpecifier, ...] = operands

        # Check if all operands are constants. A bad thing
        #   according to the B&B LGP book.
        has_register_operand: bool
        has_register_operand = any(opr[0] == StateVectorType.register
                                   for opr in operands)

        if not has_register_operand:
            raise ValueError("Operand registers are all constants")

    def __str__(self: Self) -> str:
        # Super Pythonic Code (R) (not really)

        args: str = ', '.join((name_cell_specifier(spec)
                               for spec in self.operands))
        function_name: str = getattr(self.function,
                                     '__name__',
                                     repr(self.function))

        return f"r[{self.target}] <- {function_name}({args})"

    __repr__ = __str__


class Condition[R]():
    """Base class for predicates, or conditions.

    Conditions are used by condition control structures, such as
    :class:`If` and :class:`While`.
    """
    def __init__(self: Self,
                 function: Callable[Concatenate[R, ...], bool],
                 args: tuple[CellSpecifier, ...]):
        """
        Args:
            function: TODO
            args: TODO
        """
        self.function = function
        self.args = args


class LinearProgram[R]:
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
                 registers: Iterable[R],
                 constants: Iterable[R],
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

    def set_registers(self: Self, registers: Iterable[R]) -> None:
        """Set the register vector to :arg:`registers`.
        """
        self.registers = list(registers)

    def set_constants(self: Self, constants: Iterable[R]) -> None:
        """Set the constant vector to :arg:`constants`.
        """
        self.constants = tuple(constants)

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

    def run(self: Self, instructions: Sequence[Instruction]) -> None:
        """Execute :arg:`instructions` in this context.

        Effect:
            Executing an :class:`Operation` updates
            :attr:`.registers`.
        """
        current_line: int = 0

        while current_line < len(instructions):
            current_line += self._run_instruction(instructions,
                                                  current_line)

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
                         instructions: Sequence[Instruction],
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
        instruction: Instruction = instructions[pos]
        match instruction:
            case Operation():
                return self._run_operation(instruction)
            case StructNextLine():
                return self._run_struct_next_line(instruction,
                                                  instructions,
                                                  pos)
            case StructOverLines():
                return self._run_struct_over_lines(instruction,
                                                   instructions,
                                                   pos)
            case StructUntilLabel():
                return self._run_struct_until_label(instruction,
                                                    instructions,
                                                    pos)
            case Label():
                return self._run_label(instruction)
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

    def _run_struct_over_lines(self: Self,
                               instruction: StructOverLines,
                               instructions: Sequence[Instruction],
                               pos: int) -> int:
        """Execute a structure over several lines.

        Return the number of lines actually executed.
        This is the smaller of two values:

        * The number of lines left in the program.

        * The size of the body plus one.
        """
        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  f" over next {instruction.line_count} lines.")

        collected_lines: list[Instruction] = []
        # Somehow changing `pos + 1` to `pos` works. Investigate later.
        current_pos: int = pos + 1

        num_of_steps: int = min([len(instructions) - current_pos,
                                 instruction.line_count])

        if self.verbose:
            print("Collect command into structure:")

        for _ in range(num_of_steps):
            if self.verbose:
                print(f"> {instructions[current_pos]}")

            collected_lines.append(instructions[current_pos])
            current_pos += 1
        instruction.stype(self, collected_lines)

        return num_of_steps + 1

    def _run_struct_next_line(self: Self,
                              instruction: StructNextLine,
                              instructions: Sequence[Instruction],
                              pos: int) -> Literal[1] | Literal[2]:
        """Execute a structure over the next line.

        Returns the number of lines executed (1 or 2).
        """
        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  " with next line.")

        collected_lines: list[Instruction] = []
        current_pos: int = pos + 1

        num_of_steps: int = 0 if len(instructions) == current_pos else 1

        for _ in range(num_of_steps):
            collected_lines.append(instructions[current_pos])
            current_pos += 1
        instruction.stype(self, collected_lines)

        return num_of_steps + 1

    def _run_struct_until_label(self: Self,
                                instruction: StructUntilLabel,
                                instructions: Sequence[Instruction],
                                pos: int) -> int:
        """Continue executing until a label is found.

        Return 1 if `instructions` is exhausted; otherwise return 2.
        """
        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  f" with until label {instruction.label}.")

        collected_lines: list[Instruction] = []
        current_pos: int = pos + 1

        num_of_steps: int = len(instructions) - current_pos

        if self.verbose:
            print("Collect command into structure:")

        for _ in range(num_of_steps):
            current_instruction: Instruction = instructions[current_pos]
            if self.verbose:
                print(f"> {current_instruction}")

            if (isinstance(current_instruction, Label)
                    and current_instruction.text == instruction.label):
                current_pos += 1
                break
            else:
                collected_lines.append(instructions[current_pos])
                current_pos += 1

        instruction.stype(self, collected_lines)

        return len(instructions)

    def __str__(self: Self) -> str:
        return (f"LGP execution context here. Register states:\n"
                f"> {self._get_register_states()}")

    def _get_register_states(self: Self) -> str:
        return f"r{str(self.registers)}, c{str(self.constants)}"

    __repr__ = __str__
