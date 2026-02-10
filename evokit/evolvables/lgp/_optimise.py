from ._program import Instruction
from ._program import StructureScope
from ._program import StructOverLines
from ._program import StateVectorType
from ._program import Operation
from ._program import If
from ._program import While
from ._program import Condition
from ._program import Optional
from ..primitives import gt, lt, neq
from .._common import replace_at_indices
from typing import Callable, Sequence


#: Type of an optimiser. The optimiser takes an input and
#: returns a set of indices. Instructions at these indices
#: can be skipped without affecting the program's behaviour.
type Optimiser = Callable[[Sequence[Instruction]], set[int]]


def index_introns(instructions:
                  Sequence[Instruction],
                  output_indices: set[int],
                  verbose: bool) -> set[int]:

    """Remove noneffective instructions. Return
    a set of indices, where each index locates
    an noneffective instruction.

    The algorithm is built on prior works:

    * The main algorithm extends Algorithm 3.1
        of *Linear Genetic Programming*
        (Brameier and Banzhaf, 2007) to recognise control
        structures that span more than 1 line. It also
        removes control structures whose condition
        always evaluate to ``False``.

    * The algorithm partially reinvents the I/O
        connection table from *Redundancies in Linear
        GP, Canonical Transformation, and Its Exploitation:
        a Demonstration on Image Feature Synthesis*.
    """
    # In more details, this is done with the following
    # information:
    #     * A matrix that maps each index to the index
    #     of a control structure whose scope it is in.
    #     * A matrix that maps each register to instructions
    #     that assign to its operands.

    #: `scope_matrix[i][j]` is ``True`` if the scope of
    #: `instructions[i]` includes `instructions[j]`
    scope_matrix: list[list[bool]] =\
        create_matrix((len(instructions),
                       len(instructions)), False)

    #: Indices of control statements. Useful for finding them,
    #: removing the need to iterate through `len(instructions)`
    #: indices.
    control_indices: set[int] = set()

    #: Indices for statements that are not executed. This happens
    #: if a statement is in the scope of a structure that never
    #: runs.
    noexec_indices: set[int] = set()

    # First pass. Populate `scope_matrix`, `control_indices`, and
    #   `noexec_indices`.
    for i in range(len(instructions)):
        current_instruction: Instruction = instructions[i]
        if isinstance(current_instruction, StructureScope):
            scope: int = current_instruction.scope(instructions,
                                                   i)
            scope_matrix[i][i:i + scope] = [True] * scope
            control_indices.add(i)
            if not may_run(current_instruction):
                noexec_indices.update(set(range(i, i + scope + 1)))
                # Skip loop a couple times.
                i += scope

    if verbose:
        print("$ ++ Forward pass complete. ++")
        print("$ Found control instructions at indices:"
              f" {control_indices}")
        print("$ Instructions ineffective due"
              f" to contradictory condition: {noexec_indices}")

    # We only need to keep record of variable registers,
    #   because constant registers can never be assigned to.
    #: Locations of variable registers whose values
    #: can affect at least one output register.
    effective_registers: set[int] = set(output_indices)

    #: Indices that point to effective instructions.
    effective_indices: set[int] = set()

    # Second pass. Populate `effective_registers` and
    #   `effective_indices`.
    # Note that we are iterating backwards.
    for i in range(len(instructions))[::-1]:
        current_instruction: Instruction = instructions[i]
        # If this instruction is not executed, skip it.
        if i in noexec_indices:
            continue
        # If an operation assigns to an effective register:
        #   * Add its operands effective to the set of effective
        #       registers.
        #   * Mark the operation as effective.
        match current_instruction:
            case Operation():
                if current_instruction.target in effective_registers:
                    if verbose:
                        print(f"$> Found effective operation at [{i}].")
                    effective_registers.update([
                        x[1] for x in current_instruction.operands
                        if x[0] == StateVectorType.register
                    ])
                    effective_indices.add(i)
            case StructureScope():
                match current_instruction.stype:
                    # If the structure can take arguments ...
                    case If() | While() as stype:
                        # ... check if it contains at least one effective
                        #   instruction ...
                        scope: int = current_instruction.scope(instructions,
                                                               i)
                        # ... check if it contains at least one effective
                        #   instruction. If true, then ...
                        if not set(range(i, i + scope + 1)).isdisjoint(
                            effective_indices
                        ):
                            # ... mark the instruction to be effective.
                            if verbose:
                                print("$> Found effective control"
                                    f" instruction at [{i}].")
                            effective_indices.add(i)

                            # Also, if the condition of the structure
                            #   can take arguments (i.e. not a `bool`),
                            #   then mark these register effective as well.
                            if isinstance(stype.condition, Condition):
                                effective_registers.update([
                                    x[1] for x in stype.condition.args
                                    if x[0] == StateVectorType.register
                                ])
            # If I don't know what it is, it's probably important.
            case _:
                effective_indices.add(i)

    if verbose:
        print("$ ++ Backward pass complete. ++")
        print(f"$ All effective (variable) registers: {effective_registers}")
        print(f"$ All effective instructions: {effective_indices}")
    return set(range(len(instructions))).difference(effective_indices)


def may_run(struct: StructureScope) -> bool:
    """Return if a control structure has a chance to
    execute its body. Return ``False`` if the structure
    has a condition and that condition always evaluates
    to ``False``; otherwise, return ``True``.
    """
    match struct.stype:
        case If() | While():
            match struct.stype.condition:
                case Condition() as c:
                    if c.function in {gt, lt, neq}:
                        return c.args[0] != c.args[1]
                    else:
                        return True
                case bool():
                    return struct.stype.condition
        case _:
            return True


def create_matrix[T](shape: tuple[int, int],
                     value: T) -> list[list[T]]:
    """Return a matrix of :arg:`value`\\ s with
    given :arg:`shape`.
    """
    return [[value] * shape[0]
            for _ in range(shape[0])]


def optimise_and_mask[T](instructions: Sequence[Instruction[T]],
                         output_indices: set[int],
                         verbose: bool) -> Sequence[Optional[Instruction[T]]]:
    """Optimise a sequence of instructions.
    Return a sequence where noneffective instructions
    are replaced with ``None`` and all other instructions
    remain unchanged.
    """
    indices_of_introns: set[int] = index_introns(
        instructions,
        output_indices,
        verbose
    )

    masked_instructions: Sequence[Optional[Instruction]] =\
        replace_at_indices(instructions,
                           indices_of_introns,
                           None)
    return masked_instructions


def optimise_and_reduce[T](instructions: Sequence[Instruction[T]],
                           output_indices: set[int],
                           verbose: bool) -> Sequence[Instruction[T]]:
    """Optimise a sequence of instructions.
    Return a sequence where introns are removed and
    fixed-size structures (:class:`.StructOverLines`)
    are resized accordingly.

    Costs more than :meth:`.optimise_and_mask`.
    """
    instructions = [x.copy() for x in instructions]

    indices_of_introns: set[int] = index_introns(
        instructions,
        output_indices,
        verbose
    )

    scope_matrix: list[list[bool]] =\
        create_matrix((len(instructions),
                       len(instructions)), False)
    
    rescope_scheme: list[int] = [0] * len(instructions)

    # First, build a `scope_matrix` as is done in
    # :meth:`index_introns`.
    for i in range(len(instructions)):
        current_instruction: Instruction = instructions[i]
        if isinstance(current_instruction, StructureScope):
            scope: int = current_instruction.scope(instructions,
                                                   i)
            scope_matrix[i][i:i + scope] = [True] * scope

    # This list contains all `StructOverLines`\\ s that
    #   need to be rescoped. Makes things a bit easier.
    indices_of_controls_to_rescope: set[int] = set()

    # Then, iterate through instructions backwards.
    for i in range(len(instructions))[::-1]:
        # Upon encountering an intron, ...
        if i in indices_of_introns:
            # ... find all control structures that include it, ...
            for j in range(len(instructions)):
                possible_control = instructions[j]
                if scope_matrix[j][i] and\
                        isinstance(possible_control, StructOverLines):
                    # ... and for all fixed-size structures
                    #   that happen to include the intron, shorten
                    #   the structure by 1 (to accommodate)
                    #   the removal of the intron
                    rescope_scheme[j] += 1
                    indices_of_controls_to_rescope.add(j)
        # In the end, remove the intron.

    for i in indices_of_controls_to_rescope:
        control = instructions[i]
        assert isinstance(control, StructOverLines)
        control.line_count -= rescope_scheme[i]

    for i in sorted(indices_of_introns)[::-1]:
        del instructions[i]
    return instructions
