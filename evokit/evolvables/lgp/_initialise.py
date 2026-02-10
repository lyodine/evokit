from typing import Generic, TypeVar, Self, Callable, Sequence, Optional
from ._program import StructureScope, StructureType, Type, If, For
from ._program import While, Instruction, CellSpecifier, StateVectorType
from ._program import Condition, StructOverLines, StructUntilLabel, Label
from ._program import StructNextLine
from ._program import Operation
from ._optimise import optimise_and_reduce
from ..primitives import gt, lt, geq, leq, eq, neq
from .._common import choose_k_from
from ..types import Predicate, ValueRange, Endofunction
from typing import Any
from typing import Annotated
import random
from inspect import signature
from typing import overload, Literal

R = TypeVar("R")


type Primitive[R] = Endofunction[R] | Type[StructureScope] | str


class LGPBuilder(Generic[R]):
    """Convenience factory class that creates linear programs.

    Supports a plethora of settings that fine-tune the initialisation
    process.
    """
    def __init__(self: Self,
                 primitives: Sequence[Primitive[R]],
                 register_count: int,
                 constant_count: int,
                 override_structure_types: Optional[tuple[
                     Type[StructureType]]] = None,
                 *,
                 structure_size: int | Callable[[], int] = 5,
                 for_count: int | Callable[[], int] = 5,
                 for_count_constant_ratio: Annotated[
                     float, ValueRange(0, 1)
                 ] = 5,
                 allow_replacement: bool = True,
                 allow_constant_conditions: bool = False,
                 allow_constant_operations: bool = False,
                 override_primitive_weights: Optional[Sequence[float]] = None,
                 override_logical_operators: Optional[set[Predicate]] = None):
        """
        Args:
            primitives: Building blocks for the program. Each primitive
                may be selected to form an instruction.

                If 2-tuples ``(primitive, weight)`` are given, then each
                ``primitive`` is selected with the given ``weight``.

            register_count: Number of variable registers available.

            constant_count: Number of constant registers available.

            override_structure_types: Control structure types that may
                be used to complete control structures.

                A control structure consists of two parts: a
                :class:`.StructureScope` decides its scope and
                :class:`.StructureType` decides its behaviour (e.g.
                if it is a :class:`.For` or :class:`.While` loop.

                If a :class:`.StructureScope` is selected from
                :arg:`primitives`, then one of :arg:`structure_types`
                is selected to populate it.

            structure_size: TODO

            for_count: TODO

            for_count_constant_ratio: TODO

            register_count: Number of variable registers used by the
                program.

            constant_count: Number of constant registers used by the
                program.

            allow_replacement: If ``True``, then registers are drawn
                with replacement.

            allow_constant_conditions: If ``True``, then :class:`.If`
                and :class:`.While` loops can have constant conditions.
                Such loops either always or never execute.

            allow_constant_operations: If ``True``, then
                :class:`.Operation`\\ s can have constants as all
                arguments. *Several texts call this a bad idea*.

            override_logical_operators: Logical operators that may
                be used by conditions. By default, all logical
                operators in :mod:`.primitives` are used.
        """
        # ++ Compile a list of primitives and their weights. Then,
        #   extract all labels for use by :class:`.StructUntilLabel`\\ s.
        self.primitives: tuple[Primitive, ...] = tuple(primitives)
        self.primitive_weights: Optional[tuple[float, ...]] =\
            None if override_primitive_weights is None\
            else tuple(override_primitive_weights)
        self.label_texts: tuple[str, ...] =\
            tuple(x for x in self.primitives if isinstance(x, str))

        # TODO Randomly selecting from sets is horribly slow. Oh the other
        #   hand, we do like sets for some nice operations.
        # Which is more efficient remains to be profiled.

        # ++ Pre-compile collections of registers.
        self.registers: set[CellSpecifier] =\
            set((StateVectorType.register, i) for i in range(register_count))
        self.constants: set[CellSpecifier] =\
            set((StateVectorType.constant, i) for i in range(constant_count))
        self.cells: set[CellSpecifier] = self.registers.union(self.constants)
        self.register_count_for_target_register_only: int = register_count

        # ++ Decide which structure types to draw from.
        self.structure_types = override_structure_types\
            if override_structure_types is not None\
            else (If, For, While)

        # ++ TODO I don't have time to comment these ones/
        self._meth_draw_structure_scope: Callable[[], int]
        # Define functions that draw
        if isinstance(structure_size, int):
            self._meth_draw_structure_scope =\
                lambda: random.randint(0, structure_size)
        elif callable(structure_size):
            self._meth_draw_structure_scope = structure_size
        else:
            raise TypeError("Wrong structure size.")

        self._meth_draw_for_count: Callable[[], int]
        # Define functions that draw
        if isinstance(for_count, int):
            self._meth_draw_for_count =\
                lambda: random.randint(0, for_count)
        elif callable(for_count):
            self._meth_draw_for_count = for_count
        else:
            raise TypeError("Wrong for count.")

        self.for_count_constant_ratio = for_count_constant_ratio

        self.allow_replacement = allow_replacement
        self.allow_constant_conditions = allow_constant_conditions
        self.allow_constant_operations = allow_constant_operations

        #: Logical operators that may be drawn to form conditions.
        self.logical_operators: set[Predicate]
        if override_logical_operators is None:
            self.logical_operators = {gt, lt, geq, leq, eq, neq}
        else:
            self.logical_operators = override_logical_operators

    def build(self: Self,
              length: int) -> list[Instruction[R]]:
        """Build and return a sequence of instructions
        to the given :arg:`length`.
        """
        return [
            self._build_instruction() for i in range(length)
        ]

    def _build_instruction(self: Self) -> Instruction:
        chosen_one: Primitive
        if self.primitive_weights is None:
            chosen_one = random.choice(self.primitives)
        else:
            chosen_one = random.choices(population=self.primitives,
                                        weights=self.primitive_weights)[0]

        match chosen_one:
            case str():
                return Label(chosen_one)
                # It's a label
            case type():
                return self._build_structure(chosen_one)
                # It's a StructureScope, I hope.
            case _:
                return Operation(
                    function=chosen_one,
                    target=random.randint(
                        0,
                        self.register_count_for_target_register_only),
                    operands=self._draw_cells(
                        count=_get_arity(chosen_one),
                        with_replacement=self.allow_replacement,
                        ensure_variable_register=not
                        self.allow_constant_operations
                    )
                )

    def _draw_cells(self: Self,
                    count: int,
                    with_replacement: bool,
                    ensure_variable_register: bool) -> list[CellSpecifier]:
        """Return a set of :arg:`count` :class:`.CellSpecifier`\\ s.

        Args:
            count: Number of specifiers to fetch.
            with_replacement: If ``True``, then specifiers
                are selected with replacement.
            ensure_variable_register: If ``True``, then
                the first choice is selected from just
                variable registers. This will increase the
                bias towards selecting variable registers.
        """
        if count < 1:
            return list()
        else:
            if not ensure_variable_register:
                return choose_k_from(population=tuple(self.cells),
                                     k=count,
                                     with_replacement=with_replacement)
            else:
                chosen: CellSpecifier = random.choice(tuple(self.registers))
                if with_replacement:
                    return [chosen,
                            *choose_k_from(population=tuple(self.cells),
                                           k=count - 1,
                                           with_replacement=with_replacement)]
                else:
                    return [chosen,
                            *choose_k_from(population=tuple(
                                           self.cells.difference(chosen)),
                                           k=count - 1,
                                           with_replacement=with_replacement)]

    @overload
    def _build_condition(self: Self,
                         allow_constant: Literal[True]) -> Condition | bool:
        ...

    @overload
    def _build_condition(self: Self,
                         allow_constant: Literal[False]) -> Condition:
        ...

    def _build_condition(self: Self,
                         allow_constant: bool) -> Condition | bool:
        """Return a :class:`.Condition`.

        Args:
            allow_constant: If ``True``, then ``True`` and ``False``
                are permitted as conditions.
        """
        if allow_constant:
            the_chosen_one = random.choice(tuple(
                self.logical_operators.union({True, False})))
            if isinstance(the_chosen_one, bool):
                return the_chosen_one
            else:
                return self._build_condition_from(the_chosen_one)
        else:
            return self._build_condition_from(random.choice(tuple(
                self.logical_operators)))

    def _build_condition_from(self: Self,
                              predicate: Predicate) -> Condition[R]:
        return Condition[R](function=predicate,
                            args=self._draw_cells(
                                count=_get_arity(predicate),
                                ensure_variable_register=not
                                self.allow_constant_conditions,
                                with_replacement=self.allow_replacement))

    def _build_structure(self: Self,
                         struct: Type[StructureScope]) -> StructureScope:
        if struct is StructOverLines\
                or struct is StructNextLine:
            return StructOverLines(stype=self._draw_structure_type(),
                                   line_count=self._draw_structure_scope())
        elif struct is StructUntilLabel:
            return StructUntilLabel(stype=self._draw_structure_type(),
                                    label=random.choice(self.label_texts))
        else:
            raise TypeError("The initialiser does not recognise"
                            f" initialising  {struct}"
                            " as a structure scope.")

    def _draw_structure_type(self: Self) -> StructureType:
        the_chosen_one: Type[StructureType] =\
            random.choice(self.structure_types)
        # Constructors for `If` and `While` behave the same.
        if the_chosen_one is If\
                or the_chosen_one is While:
            return the_chosen_one(condition=self._build_condition(
                self.allow_constant_conditions))
        elif the_chosen_one is For:
            return For(count=self._draw_for_exec_count())
        else:
            raise TypeError("_____________________")

    def _draw_structure_scope(self: Self) -> int:
        return self._meth_draw_structure_scope()

    def _draw_for_exec_count(self: Self) -> int | CellSpecifier:
        if random.random() > self.for_count_constant_ratio:
            return self._draw_cells(count=1,
                                    with_replacement=False,
                                    ensure_variable_register=False)[0]
        else:
            return self._meth_draw_for_count()

    def build_fully_effective(
            self: Self,
            segment_length: int,
            output_indices: set[int],
            target_length: Optional[int] = None) -> Sequence[Instruction[R]]:
        """Build and return a sequence of effective instructions.
        Do so by building sequences of :arg:`segment_length`
        instructions, then removing introns from the result.

        If a :arg:`target_length` is given, then build a new sequence
        and append it to the previous one until the accumulated
        sequence meets or exceeds :arg:`target_length`.
        May produce longer sequences as a result.
        """

        if target_length is None:
            return optimise_and_reduce(
                self.build(
                    length=segment_length
                ),
                output_indices=output_indices
            )
        else:
            accumulated_instructions = []
            while len(accumulated_instructions) < target_length:
                this_time_for_sure = optimise_and_reduce(
                    self.build(
                        length=segment_length
                    ),
                    output_indices=output_indices
                )
                accumulated_instructions.append(this_time_for_sure)

        return sum(accumulated_instructions, start=[])


def _get_arity(fun: Callable[..., Any]) -> int:
    """Copied from :mod:`.gp` and trimmed down.
    """
    if (callable(fun)):
        return len(signature(fun).parameters)
    else:
        # Shouldn't run if types check out ... just in case.
        raise TypeError("Trying to inspect non-callable")
