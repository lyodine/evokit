from __future__ import annotations

# It's just so appropriate here.
# I'm coming back to this comment and have no idea
#   what it means.
# Luckily I have stuck to the principle of not joking
#   anywhere that matters, so it's probably no big deal.
# On well.
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


class Instruction():
    pass


class StructureType(ABC):
    """Base class for all control structure types.

    The :class:`.StructureType` decides how many times
    a control structure is executed: whether once
    (:class:`.If`), for a number of times (:class:`.For`),
    or until an expression evaluates to ``True`` (:class:`.While`).

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

    The scope decides decides how many lines following the
    current line become part of the structure (its _body_).
    The scope also contains a :class:`.StructureScope`,
    which decides how many times the body is executed.

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
    """Simple "for" loop.

    A control structure with this type repeats its body for
    :attr:`.count` times.
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
    until :attr:`.condition` is satisfied or
    :attr:`.loop_cap` loops have elapsed.

    .. info::

        To prevent infinite execution, this structure
        is a glorified *for* loop.
    """

    #: Maximum number of iterations a :class:`While` loop can run for.
    loop_cap = 20

    def __init__(self: Self, conditional: Condition):
        """
        Args:
            conditional: Condition that, if satisfied, ends the structures.
        """
        #: Condition that must be satisfied for the structure to stop.
        self.condition = conditional

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
    """Structure with conditional execution.

    A control structure with this type executes once if :arg:`conditional`
    is satisfied. Otherwise, the structure is skipped and does nothing.
    """
    def __init__(self: Self, conditional: Condition):
        self.conditional = conditional

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        if (lgp.check_condition(self.conditional)):
            lgp.run(instructions)


@dataclass
class ValueRange:
    min: float
    max: float


class StateVectorType(Enum):
    """Type of a state vector.

    A linear program stores three state vectors:
    the input vector :attr:`.LinearProgram.inputs`,
    the mutable register :attr:`.LinearProgram.registers`, and
    the constant register :attr:`.LinearProgram.constants`,
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
    if spec[0] == StateVectorType.register:
        return f"r[{spec[1]}]"
    else:
        return f"c[{spec[1]}]"


def cell(pos: int) -> CellSpecifier:
    """Convenience function for creating a :class:`.CellSpecifier`.

    Arg:
        pos: If :arg:`pos>=0`, specify the :arg:`pos`\\ :sup:`th`
            register. Otherwise, specify the  :arg:`abs(pos)-1`
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


type Endofunction[R] = Callable[Concatenate[R, ...], R]


@dataclass
class Operation[R](Instruction):
    """An operation.

    Executing this operation calls :arg:`function`
    with :attr:`.operands` as arguments. The result
    is then deposited into the :attr:`.target`\\ s
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
        # Do not, however, check if the target is a register, because
        #   :attr:`.inputs` and :attr:`.constants` are already immutable.
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

    Conditions are used by conditional control structures, such as
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
        """Update the register vector with :arg:`registers`.
        """
        self.registers = list(registers)

    def set_constants(self: Self, constants: Iterable[R]) -> None:
        """Update the constant vector with :arg:`constants`.
        """
        self.constants = tuple(constants)

    def get_cell_value(self: Self,
                       cellspecifier: CellSpecifier) -> R:
        """Return the state vector specified by :arg:`cellspec`.
        """

        return self.get_state_vector(
            cellspecifier[0])[cellspecifier[1]]

    def get_state_vector(self: Self,
                         celltype: StateVectorType)\
            -> Sequence[R]:
        """Return the state vector specified by :arg:`cellspec`.
        """
        match celltype:
            case StateVectorType.register:
                return self.registers
            case StateVectorType.constant:
                return self.constants

    def run(self: Self, instructions: Sequence[Instruction]) -> None:
        """Execute :arg:`instructions` in this context.

        Effect:
            Instructions, for example :class:`Operation` s, may alter
            the state of this context.
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

        Execute the instruction :arg:`instruction`
        in sequence :arg:`instructions` at position :arg:`pos`.

        Return the number of lines advanced as a result.
        Running a single operation advances the execution
        pointer by 1; running control structures may
        skip more lines.

        Args:
            instructions: Sequence of instruction to run :arg:`instruction` in.

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
        if self.verbose:
            print(f"{instruction.text}: (label)")
        return 1

    def _run_operation(self: Self,
                       instruction: Operation) -> Literal[1]:
        """Execute :arg:`instruction` in this context.
        Returns the number of lines executed, which is always 1.
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
                              pos: int) -> int:
        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  " with next line.")

        collected_lines: list[Instruction] = []
        current_pos: int = pos + 1

        num_of_steps: int = min([len(instructions) - current_pos, 1])

        for _ in range(num_of_steps):
            collected_lines.append(instructions[current_pos])
            current_pos += 1
        instruction.stype(self, collected_lines)

        return num_of_steps

    def _run_struct_until_label(self: Self,
                                instruction: StructUntilLabel,
                                instructions: Sequence[Instruction],
                                pos: int) -> int:
        if self.verbose:
            print(f"Running {type(instruction.stype).__name__}"
                  f" with until label {instruction.label}.")

        collected_lines: list[Instruction] = []
        current_pos: int = pos + 1

        num_of_steps: int = len(instructions) - current_pos

        for _ in range(num_of_steps):
            current_instruction: Instruction = instructions[current_pos]

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
