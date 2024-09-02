from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from typing import Tuple
    from typing import Dict
    from typing import List
    from typing import Any
    from typing import Self
    from typing import Callable
    from typing import Iterable
    from typing import Sequence
    from typing import Type

from typing import TypeVar

from operator import itemgetter

from itertools import chain
from abc import abstractmethod
from typing import override
from ..core import Variator

import abc
import functools
import math
import random
import typing
from inspect import signature
import random
from typing import Generic

from ..core import Evaluator, Individual


T = TypeVar("T")

_EXPR_PARAM_PREFIX: str = "x"


def _get_arity(fun: Any) -> int:
    """Return the arity of an object.

    If the argument is callable, return the length of its signature.
    Otherwise, return 0.

    Does not work with built-in functions and other objects that do not
    work with :meth:`.inspect.signature`.

    Args:
        fun: An object
    """
    if (callable(fun)):
        return len(signature(fun).parameters)
    elif isinstance(fun, Expression):
        # Specialised code for programs
        return fun.arity
    elif isinstance(fun, Symbol):
        # Specialised code for programs
        return 0
    else:
        return 0

class Expression(Generic[T]):
    """A node in an expression tree.

    Recursive data structure that implements program trees. An ``Expression``
    is also a :class:`Callable` that only accepts arguments passed by position.

    The attribute :attr:`.value` 
    """
    def __init__(self: Self,
                 arity: int,
                 value: T | Callable[..., T] | Symbol,
                 children: List[Expression[T]],
                 factory: Optional[ExpressionFactory] = None):
        #! Arity of the expression node.
        self.arity: int = arity
        #! Value of the expression node.
        self.value: T | typing.Callable[..., T] | Symbol = value
        #! Children of the expression node.
        self.children = children
        
        self._factory = factory

    @property
    def factory(self: Self) -> ExpressionFactory[T]:
        """The :class:`.ExpressionFactory`, if any, that built this object.

        The :class:`.ExpressionFactory` maintains hyperparameters that
        instruct the construction of this object.
        """
        if self._factory is not None:
            return self._factory
        else:
            raise ValueError("This expression is not associated with a factory.")
    
    @factory.setter
    def factory(self: Self, factory: ExpressionFactory[T]) -> None:
        self._factory = factory

    def __call__(self: Self, *args: T) -> T:
        """Evaluate the expression tree with arguments.

        Recursively evaluate expression nodes in :attr:`children`. Then,
        apply :attr:`value` to the results, in the same order as the
        :attr:`children` they are resolved from.

        Args:
            *args: Arguments to the program.
        """
        self_arity: int = self.arity
        params_arity: int = len(args)
        if (self_arity != params_arity):
            raise ValueError(f"The expression expects"
                             f"{self_arity} parameters, "
                             f"{params_arity} given.")

        value_arity: int = _get_arity(self.value)
        children_arity: int = len(self.children)

        if (value_arity != children_arity):
            raise ValueError(f"The node may be improperly configured. The value expects"
                             f"{value_arity} arguments, while "
                             f"{value_arity} children are given.")

        # Evaluate children, pack results into a generator
        results = (x(*args) for x in self.children)

        if callable(self.value):
            return self.value(*results)
        if isinstance(self.value, Symbol):
            return args[self.value.pos]
        else:
            return self.value

    def copy(self: Self) -> Self:
        """Return a deep copy.

        Call the `python`:copy(self, ...): method on :attr:`value`,
        each item in :attr:`children`, and :attr:`value` (if :attr:`value`
        implements a method named ``copy``). Use the results to create
        a new :class:`Expression`
        """
        new_value: T | Callable[..., T] | Symbol
        if (hasattr(self.value, "copy") and callable(getattr(self.value,'copy'))):
            new_value = getattr(self.value,'copy')()
        else:
            new_value = self.value

        new_children: List[Expression[T]] = [x.copy() for x in self.children]

        return self.__class__(self.arity, new_value, new_children, self.factory)

    def nodes(self: Self) -> Tuple[Expression[T], ...]:
        """Return a flat list view of all nodes and subnodes.
        
        Note that operations performed on items in the returned list affect
        the original objects.
        """
        return (self, *(chain.from_iterable((x.nodes() for x in self.children))))

    def __str__(self: Self) -> str:
        delimiter = ", "

        my_name: str = self.value.__name__\
            if callable(self.value) else str(self.value)

        children_name: str
        if len(self.children) < 1:
            children_name = ""
        else:
            children_name = f"({functools.reduce(
                lambda x, y: str(x) + delimiter + str(y),
                [str(x) for x in self.children])})"

        return (f"{my_name}{children_name}")
    
class Symbol():
    """Dummy object used by :class:`.ExpressionFactory`.

    See:
        ??? TODO
    """
    __slots__ = ['pos']
    def __init__(self: Self, pos: int):
        self.pos: int = pos
    
    def __str__(self:Self) -> str:
        global _EXPR_PARAM_PREFIX
        return _EXPR_PARAM_PREFIX + str(self.pos)

class ExpressionFactory(Generic[T]):
    """Factory class for :class:`Expression`.

    Build :class:`Expression` with supplied hyperparameters. Then,
    register itself with each created object by setting its 
    :attr:`Expression.factory` attribute.

    Note:
        If ``arity = 0``, then ``primitives`` must include at least one literal.
        Otherwise, the tree cannot be built, as no terminal node can be drawn.

    See:
        :attr:`Expression.factory`
    """
    def __init__(self: Self,
                 primitives: Tuple[T | Callable[..., T], ...],
                 arity: int):
        """
        Args:
            primitives: instructions and terminals that occupy nodes of the
            expression tree. Listing a primitive more than once increases its
            chance of being selected.

            arity: arity of constructed :class:`Expression` instances.

        Raise:
            ValueError if ``arity=0`` and ``primitives`` does not contain nullary
            values. The tree cannot be built without terminals.
        """
        
        self.primitive_pool: Dict[int, List[T | Callable[..., T] | Symbol]] = {}
        
        self.arity = arity

        self.primitive_pool[0] = []

        for item in primitives:
            item_arity: int = _get_arity(item)
            if item_arity not in self.primitive_pool:
                self.primitive_pool[item_arity] = []

            self.primitive_pool[item_arity].append(item)

        for i in range(arity):
            self.primitive_pool[0].append(Symbol(i))

        if not self.primitive_pool[0]:
            # Remember to test it
            raise ValueError("Factory is initialised with no terminal node.")

    def _build_is_node_overbudget(self: Self) -> bool:
        return self._temp_node_budget_used > self._temp_node_budget_cap

    def _build_cost_node_budget(self: Self, cost: int) -> None:
        self._temp_node_budget_used += cost

    def _build_initialise_node_budget(self, node_budget: int) -> None:
        self._temp_node_budget_cap: int = node_budget
        self._temp_node_budget_used: int = 0

    def build(self: Self,
              node_budget: int,
              layer_budget: int,
              nullary_ratio: Optional[float] = None) -> Expression:
        """Build an expression tree to specifications.

        The parameters ``node_budget`` and ``layer_budget`` are not constraints.
        Rather, if the tree exceeds these budgets, then only nullary values
        can be drawn. This ensures that the tree does not exceed these budgets by
        too much.

        Costs are incurred after a batch nodes are drawn.

        Args:
            node_budget: Total number of nodes in the tree
            layer_budget: Depth of the tree
            nullary_ratio: Probability of drawing a nullary node

        Raise:
            ``ValueError`` if ``nullary_ratio`` lies outside of range ``[0,1]``
        """
        if (nullary_ratio is not None and
           (nullary_ratio < 0 or nullary_ratio > 1)):
            raise ValueError(f"Probability of drawing nullary values must be"
                             f"between 1 and 0. Got: {nullary_ratio}")

        self._build_initialise_node_budget(node_budget)

        return self._build_recurse(layer_budget, nullary_ratio)

    def _build_recurse(self: Self,
                       layer_budget: int,
                       nullary_ratio: Optional[float] = None) -> Expression[T]:

        # Get the new node value
        new_node: Expression[T]

        target_primitive: T | Callable[..., T] | Symbol =\
                            self.draw_primitive(1) if layer_budget < 1\
                            else self.draw_primitive(nullary_ratio)
        
        inferred_value_arity = _get_arity(target_primitive)

        return Expression(arity = self.arity,
                          value = target_primitive,
                          children = [*(self._build_recurse(layer_budget-1, nullary_ratio)
                            for _ in range(inferred_value_arity))],
                          factory = self)

    def draw_primitive(self: Self,
                       nullary_ratio: Optional[float] = None,
                       free_draw: bool = False) -> T | Callable[..., T] | Symbol :
        """Return an item from :attr:`primitive_pool`

        Args:
            nullary_ratio: probability of drawing terminals. If set, non-terminals
            are drawn with probability (:python:`1-nullary_ratio`).

            free_draw: if ``True``, then the call does not affect or respect
            constraints on node counts. For example, it can still draw non-terminal
            nodes, even while exceeding node count and depth constraints.
        """
        if (self._build_is_node_overbudget() and not free_draw):
            nullary_ratio = 1

        value_pool: List[T | Callable[..., T] | Symbol]

        if (nullary_ratio is None):
            value_pool = list(
                chain.from_iterable(self.primitive_pool.values()))
        else:
            nullary_random = random.random()
            if (nullary_random < nullary_ratio):
                value_pool = self.primitive_pool[0]
            else:
                value_pool = list(chain.from_iterable(
                    self.primitive_pool[x] for x in self.primitive_pool.keys() if x != 0))

        if not free_draw:
            self._build_cost_node_budget(1)

        return random.choice(value_pool)
    
    def primitive_by_arity(self: Self,
                           arity: int) -> T | Callable[..., T] | Symbol :
        """Draw a instruction or terminal of the given arity.

        If no primitive of the given arity exists, return an empty list.
        """
        return random.choice(self.primitive_pool[arity])
    
class Program(Individual[Expression[T]]):
    """A tree-based genetic program.
    """
    def __init__(self, expr: Expression[T]):
        self.genome: Expression[T] = expr

    def __str__(self) -> str:
        return f"Program:{str(self.genome)}"

    def copy(self) -> Self:
        return self.__class__(self.genome.copy())


class ProgramFactory(Generic[T]):
    """Convenience factory class for :class:`Program`.

    Contain an :class`ExpressionFactory` instance. Delete storage of
    hyperparameters and :meth:`ProgramFactory.build` to the internal
    :class`ExpressionFactory`.
    """
    def __init__(self: Self, primitives: Tuple[T | Callable[..., T], ...], arity: int):
        self.exprfactory = ExpressionFactory[T](primitives = primitives,
                                                arity = arity)

    def build(self: Self,
              node_budget: int,
              layer_budget: int,
              nullary_ratio: Optional[float] = None) -> Program:
        # new_deposit = [x.copy() for x in self.symbol_deposit]
        return Program(self.exprfactory.build(node_budget, layer_budget, nullary_ratio))



class CrossoverSubtree(Variator[Program[float]]):
    """Crossover operator that randomly exchange subtrees of parents.

    Select an internal node from each parent. Then, select one
    child of each internal node and exchange these child nodes. Doing
    so also exchanges subtrees that begin at these child nodes.
    """
    def __init__(self, shuffle: bool = False):
        """
        Args:
            shuffle: If ``True``: collect all child nodes of both
            internal nodes into one list, shuffle that list, then assign
            items back to respective parents.
        """
        self.arity = 2
        self.coarity = 2
        self.shuffle = shuffle

    def vary(self,
             parents: Sequence[Program[float]]) -> Tuple[Program[float], ...]:

        root1: Program = parents[0].copy()
        root2: Program = parents[1].copy()
        root1_pass: Program = parents[0].copy()
        root2_pass: Program = parents[1].copy()
        # print(f"root 1: {str(root1)}")
        # print(f"root 2: {str(root2)}")
        internal_nodes_from_root_1 =\
            tuple(x for x in root1.genome.nodes() if len(x.children) > 0)
        internal_nodes_from_root_2 =\
            tuple(x for x in root2.genome.nodes() if len(x.children) > 0)
        # print(f"root 1 i.nodes: {str([str(x) for x in internal_nodes_from_root_1])}")
        # print(f"root 2 i.nodes: {str([str(x) for x in internal_nodes_from_root_2])}")

        # If both expression trees have valid internal nodes, their
        #   children can be exchanged.
        if (internal_nodes_from_root_1 and internal_nodes_from_root_2):
            if (not self.shuffle):
                self.__class__._swap_children(
                    random.choice(internal_nodes_from_root_1),
                    random.choice(internal_nodes_from_root_2))
            else:
                self.__class__._shuffle_children(
                    random.choice(internal_nodes_from_root_1),
                    random.choice(internal_nodes_from_root_2))
            
            # expression_node_from_root_1_to_swap =\
            #     random.choice(internal_nodes_from_root_1)
            # expression_node_from_root_2_to_swap =\
            #     random.choice(internal_nodes_from_root_2)
        return (root1, root2, root1_pass, root2_pass)
            
    @staticmethod
    def _swap_children(expr1: Expression[float], expr2: Expression[float]) -> None:
        r1_children = expr1.children
        r2_children = expr2.children

        r1_index_to_swap = random.randint(0, len(expr1.children) - 1)
        r2_index_to_swap = random.randint(0, len(expr2.children) - 1)

        r2_index_hold = r2_children[r2_index_to_swap].copy()
        r2_children[r2_index_to_swap] = r1_children[r1_index_to_swap].copy()
        r1_children[r1_index_to_swap] = r2_index_hold.copy()

    @staticmethod
    def _shuffle_children(expr1: Expression[float], expr2: Expression[float]) -> None:
        child_nodes = list(expr1.children + expr2.children)
        random.shuffle(child_nodes)

        for i in range(0, len(expr1.children)):
            expr1.children[i] = child_nodes[i].copy()

        for i in range(-1, -(len(expr2.children) + 1), -1):
            expr2.children[i] = child_nodes[i].copy()


# class CrossoverSubtree(Variator[Program[float]]):
#     def __init__(self):
#         self.arity = 1
#         self.coarity = 1

#     def vary(self,
#              parents: Sequence[Program[float]]) -> Tuple[Program[float], ...]:

#         root1: Program = parents[0].copy()
#         random_node = random.choice(root1.genome.nodes())  

class MutateNode(Variator[Program]):
    """Mutator that changes the primitive in a uniformly random node to
    a uniformly selected primitive of the same arity.
    """
    def __init__(self: Self) -> None:
        self.arity = 1
        self.coarity = 1

    def vary(self: Self,
             parents: Sequence[Program]) -> Tuple[Program, ...]:
        """
        Args:
            parents: collection where the 0th item is the parent.
        
        Raise:
            ``ValueError`` if the parent's :attr:`Program.genome`
            does not have :attr:`Expression.factory` set.
        """
        root1: Program = parents[0].copy()
        if root1.genome.factory is None:
            raise ValueError("") 
        root_pass: Program = parents[0].copy()
        random_node = random.choice(root1.genome.nodes())
        random_node.value = root1.genome.factory.primitive_by_arity(
                                _get_arity(random_node.value))
        
        random_node.value = root1.genome.factory.primitive_by_arity(
                                _get_arity(random_node.value))
        
        return (root1, root_pass)
    
class MutateSubtree(Variator[Program]):
    """Mutation operator that randomly mutates subtrees.

    Uniformly select an internal node, then uniformly select a child of
    that node. Replace that child with a subtree, constructed by calling
    :meth:`ExpressionFactory.build` of the associated :class:`ExpressionFactory`
    found in :attr:`Expression.factory`.
    """
    def __init__(self: Self, node_budget: int, layer_budget: int, nullary_ratio: Optional[float] = None) -> None:
        self.arity = 1
        self.coarity = 2
        self.node_budget = node_budget
        self.layer_budget = layer_budget
        self.nullary_ratio = nullary_ratio

    def vary(self: Self,
             parents: Sequence[Program]) -> Tuple[Program, ...]:
        
        root1: Program = parents[0].copy()
        root_pass: Program = parents[0].copy()
        internal_nodes: Tuple[Expression, ...] =\
                tuple(x for x in root1.genome.nodes() if len(x.children) > 0)

        if (internal_nodes):
            random_internal_node = random.choice(internal_nodes)
            index_for_replacement = random.randint(0, len(random_internal_node.children)-1)
            random_internal_node.children[index_for_replacement] = \
                    random_internal_node.factory.build(self.node_budget,
                                                self.layer_budget,
                                                self.nullary_ratio)

        return (root1, root_pass)


class SymbolicEvaluator(Evaluator[Program[float]]):
    """Evaluator for symbolic regression.

    Compare the output of a program tree against a given
    objective function, over a fixed set of points. Assign higher
    fitness to programs whose output is closer to that of
    the objective function.
    """
    def __init__(self,
                 objective: Callable,
                 support: Tuple[Tuple[float, ...], ...]):
        """
        Args:
            objective: function that 
            support: collection of points on which the program
            is compared against ``objective``.

        Raise:
            TypeError if the first item in ``support`` does not
            match the arity of ``objective``.
        """
        self.objective = objective
        self.support = support
        self.arity = _get_arity(objective)

        if self.arity != len(support[0]):
            raise TypeError(f"The objective function has arity "
                            f"{self.arity}, the first item in support has arity "
                            f"{support[0]}; they are not the same.")

    def evaluate(self, program: Program[float]) -> float:
        return -sum([abs(self.objective(*sup) - program.genome(*sup)) for sup in self.support])

class PenaliseNodeCount(Evaluator[Program[float]]):
    """Evaluator that favours smaller program trees.

    For each node in the given program tree,
    incur a penalty of ``coefficient``.
    """
    def __init__(self, coefficient: float):
        """
        Args:
            coefficient: penalty coefficient for each node in the
            program tree.
        """
        self.coefficient = coefficient

    def evaluate(self, program: Program[float]) -> float:
        return -(self.coefficient * len(program.genome.nodes()))
