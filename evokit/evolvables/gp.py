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
    """Inspect the arity of an object

    Return the signature length of a callable. If the input is not callable,
        return 0.

    Args:
        fun: An object

    Return:
        The arity of `fun`

    Todo:
        Once *lambda masquerade* is implemented, remove the special case for GP.
    """
    if (callable(fun)):
        return len(signature(fun).parameters)
    elif isinstance(fun, ExpressionBranch):
        # Specialised code for programs
        return len(fun.children)
    else:
        return 0

class Expression(abc.ABC, Generic[T]):
    def __init__(self: Self, arity: int)-> None:
        self.arity: int = arity
        self.children: List[Expression[T]]

    @abstractmethod
    def __call__(self: Self, *params: T) -> T: ...

    @abstractmethod
    def copy(self: Self) -> Self: ...

    @abstractmethod
    def nodes(self: Self) -> Tuple[Expression[T], ...]: ...

    @abstractmethod
    def __str__(self: Self) -> str: ...

    @abstractmethod
    def __repr__(self: Self) -> str: ...



class ExpressionSymbol(Expression[T]):
    def __init__(self: Self, arity: int, pos: int) -> None:
        super().__init__(arity)
        global _EXPR_PARAM_PREFIX
        self.pos: int = pos
        self.__name__: str = _EXPR_PARAM_PREFIX + str(self.pos)

        #! Children of the expression node
        self.children: List[Expression[T]] = []

    @override
    def __call__(self: Self, *args: T) -> T:
        self_arity: int = self.arity
        params_arity: int = len(args)
        if (self_arity != params_arity):
            raise ValueError(f"The expression expects "
                             f"{self_arity} parameters, "
                             f"{params_arity} given.")
        return args[self.pos]

    @override
    def copy(self: Self) -> Self:
        return self.__class__(self.pos, self.arity)

    @override
    def nodes(self) -> Tuple[Expression[T], ...]:
        return ()

    @override
    def __str__(self: Self) -> str:
        return self.__name__

    @override
    def __repr__(self: Self) -> str:
        return f"ExpressionSymbol({self.__name__})"


class ExpressionBranch(Expression[T]):
    """Recursive data structure of a program tree.

    An instance of this class represents an expression node. A expression node
    and its children forms a expression tree.
    """
    def __init__(self: Self,
                 arity: int,
                 value: T | Callable[..., T],
                 children: Optional[List[Expression[T]]] = None):
        super().__init__(arity)
        #! Value of the expression node.
        self.value: T | typing.Callable[..., T] = value
        #! Children of the expression node
        self.children: List[Expression[T]]
        
        if children is not None:
            self.children = children
        #! Arity of the expression as a ``Callable``
        # self.arity = _get_arity(self.value)
        

    def set_children(self, *children: Expression[T]) -> None:
        value_arity: int = _get_arity(self.value)
        children_arity: int = len(children)

        if (value_arity != children_arity):
            raise ValueError(f"When constructing the branch node, the value expects"
                             f"{value_arity} arguments, "
                             f"{value_arity} children defined.")

        self.children = list(children)

    def __call__(self: Self, *args: T) -> T:
        """Evaluate the expression tree.

        Recursively evaluate expression nodes in :attr:`children`. Then,
        apply :attr:`value` to the results, in the same order as the
        :attr:`children` they are resolved from.
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
        else:
            return self.value

    def copy(self: Self) -> Self:
        """Return a copy of the current node and all subnodes.

        Call the `python`:copy(self, ...): method on :attr:`value`,
        each item in :attr:`children`, and :attr:`value` (if :attr:`value`
        implements a method named ``copy``). Use the results to create
        a new :class:`Expression`
        """
        new_value: T | Callable[..., T]
        if (hasattr(self.value, "copy") and callable(getattr(self.value,'m'))):
            new_value = getattr(self.value,'m')('copy')
        else:
            new_value = self.value

        new_children: List[Expression[T]] = [x.copy() for x in self.children]

        return self.__class__(self.arity, new_value, new_children)

    def nodes(self) -> Tuple[Expression[T], ...]:
        """
        TODO What? Be wary of misuse.
        """
        return (self, *(chain.from_iterable((x.nodes() for x in self.children))))

    def __str__(self) -> str:
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

    @override
    def __repr__(self: Self) -> str:
        return f"ExpressionSymbol(pass)"
    
class Symbol():
    __slots__ = ['pos']
    def __init__(self, pos: int):
        self.pos: int = pos

class ExpressionFactory(Generic[T]):
    """Factory class for :class:`Expression`.

    Receive a collection of primitives, then build :class:`Expression`
    instances whose :attr:`Expression.value` draw from this collection.
    """
    def __init__(self, primitives: Tuple[Callable[..., T], ...], arity: int):
        """Mappings from arity to a list of primitives of that arity.

        Note that both terminals and nullary callables have arity 0.
        """
        self.primitive_pool: Dict[int, List[T | Callable[..., T] | Symbol]] = {}
        self.arity = arity

        # There should always be nullary functions.
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

    def _build_is_node_overbudget(self) -> bool:
        return self._temp_node_budget_used > self._temp_node_budget_cap

    def _build_cost_node_budget(self, cost: int) -> None:
        self._temp_node_budget_used += cost

    def _build_initialise_node_budget(self, node_budget: int) -> None:
        self._temp_node_budget_cap: int = node_budget
        self._temp_node_budget_used: int = 0

    def build(self,
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

        """
        if (nullary_ratio is not None and
           (nullary_ratio < 0 or nullary_ratio > 1)):
            raise ValueError(f"Probability of drawing nullary values must be"
                             f"between 1 and 0. Got: {nullary_ratio}")

        self._build_initialise_node_budget(node_budget)

        return self._build_recurse(layer_budget, nullary_ratio)

    def _build_recurse(self,
                       layer_budget: int,
                       nullary_ratio: Optional[float] = None) -> Expression[T]:

        # Get the new node value
        new_node: Expression[T]

        if (layer_budget < 1):
            return self.draw_node(1)
        else:
            new_node = self.draw_node(nullary_ratio)
            if isinstance(new_node, ExpressionBranch):
                inferred_value_arity: int = _get_arity(new_node.value)
                new_node.set_children(
                    *(self._build_recurse(layer_budget,nullary_ratio)
                      for _ in range(inferred_value_arity)))
            
            return new_node
                
        
    def draw_node(self,
                  nullary_ratio: Optional[float] = None,
                  free_draw: bool = False) -> Expression[T]:
        """
        """
        target_primitive = self.draw_primitive(nullary_ratio, free_draw)

        if isinstance(target_primitive, Symbol):
            return ExpressionSymbol(self.arity, target_primitive.pos)
        else:
            return ExpressionBranch(self.arity, target_primitive)

    def draw_primitive(self,
                       nullary_ratio: Optional[float] = None,
                       free_draw: bool = False) -> T | Callable[..., T] | Symbol :
        
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


a = ExpressionSymbol(4, 0)

print(a(1,2,3,4))
# NODE_BUDGET = 10
# LAYER_BUDGET = 2

# from .funcs import *


# a = ExpressionFactory((add, sub, mul, div, sin, cos), 5)

# expr = a.build(NODE_BUDGET, LAYER_BUDGET)
# print(expr)
# print(expr())


# class ProgramFactory(Generic[T]):
#     def __init__(self, functions: Tuple[T | Callable[..., T], ...], arity):
#         self.arity = arity
#         self.symbol_deposit: List[Symbol] = []
#         self._next_symbol_name_to_dispatch = 0

#         for _ in range(0, arity):
#             self.symbol_deposit.append(self._new_symbol())

#         self.exprfactory = ExpressionFactory[T](functions + tuple(self.symbol_deposit))

#     def _new_symbol(self) -> Symbol[T]:
#         return Symbol(self._dispatch_symbol_name())

#     def _dispatch_symbol_name(self) -> str:
#         self._next_symbol_name_to_dispatch += 1
#         return "s_" + str(self._next_symbol_name_to_dispatch)

#     def build(self,
#               node_budget: int,
#               layer_budget: int,
#               nullary_ratio: Optional[float] = None) -> Program:
#         # new_deposit = [x.copy() for x in self.symbol_deposit]
#         return Program(self.exprfactory.build(node_budget, layer_budget, nullary_ratio),
#                        self.symbol_deposit,
#                        factory = self)

# # Note that programs from the same factory share the same set of argument values.
# # This should be desirable - and well hidden - if the object is only shared by one thread.
# # I'm not prepared to deal with concurrency.

# class Program(Individual[T]):
#     """

#     """
#     def __init__(self, expr: Expression[T], symbols: List[Symbol],
#                  factory: ProgramFactory[T]):
#         self.genome: Expression[T] = expr
#         self.symbols: List[Symbol] = symbols
#         self.factory = factory

#     def evaluate_with_args(self, *args: T) -> T:
#         expected_arity: int = len(self.symbols)
#         parameter_arity:int = len(args)

#         if (expected_arity != parameter_arity):
#             raise TypeError(
#                 f"The program is expecting {expected_arity} arguments,"
#                 f"got {parameter_arity}.")

#         for i in range(len(self.symbols)):
#             self.symbols[i].assign(args[i])
#         return self.genome.evaluate()

#     def __call__(self, *args: T) -> T:
#         return self.evaluate_with_args(*args)

#     def __str__(self) -> str:
#         return str(self.genome)

#     def copy(self) -> Self:
#         return self.__class__(self.genome.copy(),
#                               self.symbols, ## warning!!!
#                               factory = self.factory)


# class ProgramCrossoverVariator(Variator[Program[float]]):
#     def __init__(self):
#         self.arity = 2
#         self.coarity = 2

#     def vary(self,
#              parents: Sequence[Program[float]]) -> Tuple[Program[float], ...]:

#         root1: Program = parents[0].copy()
#         root2: Program = parents[1].copy()
#         # print(f"root 1: {str(root1)}")
#         # print(f"root 2: {str(root2)}")

#         nodes_from_root_1 = root1.genome.nodes()
#         nodes_from_root_2 = root2.genome.nodes()
#         # print(f"root 1 nodes: {str([str(x) for x in nodes_from_root_1])}")
#         # print(f"root 2 nodes: {str([str(x) for x in nodes_from_root_2])}")

#         # Select internal nodes, these nodes have children.
#         internal_nodes_from_root_1 =\
#             tuple(x for x in nodes_from_root_1 if len(x.children) > 0)
#         internal_nodes_from_root_2 =\
#             tuple(x for x in nodes_from_root_2 if len(x.children) > 0)
#         # print(f"root 1 i.nodes: {str([str(x) for x in internal_nodes_from_root_1])}")
#         # print(f"root 2 i.nodes: {str([str(x) for x in internal_nodes_from_root_2])}")

#         # If both expression trees have valid internal nodes, their
#         #   children can be exchanged.
#         if (internal_nodes_from_root_1 and internal_nodes_from_root_2):
#             expression_node_from_root_1_to_swap =\
#                 random.choice(internal_nodes_from_root_1)
#             expression_node_from_root_2_to_swap =\
#                 random.choice(internal_nodes_from_root_2)
#             self.__class__._swap_children(
#                 expression_node_from_root_1_to_swap, expression_node_from_root_2_to_swap)


#         # print(f"Xoot 1: {str(root1)}")
#         # print(f"Xoot 2: {str(root2)}")

#         return (root1, root2)

#     @staticmethod
#     def _swap_children(expr1: Expression[float], expr2: Expression[float]) -> None:
#         """... or, shuffle_children would be a more appropriate name.
#         Randomly exchange children of two members.
#         """
#         r1_children = expr1.children
#         r2_children = expr2.children

#         r1_index_to_swap = random.randint(0, len(expr1.children) - 1)

#         r2_index_to_swap = random.randint(0, len(expr2.children) - 1)

#         r2_index_hold = r2_children[r2_index_to_swap].copy()
#         r2_children[r2_index_to_swap] = r1_children[r1_index_to_swap].copy()
#         r1_children[r1_index_to_swap] = r2_index_hold.copy()

#     @staticmethod
#     def _shuffle_children(expr1: Expression[float], expr2: Expression[float]) -> None:
#         child_nodes = list(expr1.children + expr2.children)
#         random.shuffle(child_nodes)

#         for i in range(0, len(expr1.children)):
#             expr1.children[i] = child_nodes[i].copy()

#         for i in range(-1, -(len(expr2.children) + 1), -1):
#             expr2.children[i] = child_nodes[i].copy()

# class ProgramNodeMutationVariator(Variator[Program[float]]):
#     def __init__(self, mutation_rate: float, nullary_ratio = 0):
#         self.arity = 1
#         self.coarity = 1
#         self.mutation_rate = mutation_rate
#         self.nullary_ratio = nullary_ratio

#     def vary(self,
#              parents: Tuple[Program[float], ...]) -> Tuple[Program[float], ...]:
#         root: Program = parents[0].copy()
#         root.genome.value =\
#             root.factory.exprfactory.poll_function(self.nullary_ratio,
#                                                    free_draw=True)
#         return (root,)



# class SymbolicEvaluator(Evaluator[Program[float]]):
#     def __init__(self, objective: Callable, support: Tuple[Tuple[float, ...], ...]):
#         self.objective = objective
#         self.support = support
#         self.arity = _get_arity(objective)
#         if self.arity != len(support[0]):
#             raise TypeError("aaaaaaah")

#     def evaluate(self, program: Program[float]) -> float:
#         if self.arity != _get_arity(program):
#             raise TypeError("what")
#         return -sum([abs(self.objective(*sup) - program(*sup)) for sup in self.support])

# class SmallerIsBetter(Evaluator[Program[float]]):
#     def evaluate(self, program: Program[float]) -> float:
#         return -len(program.genome.nodes())


# # class GymEvaluator(Evaluator[Program[float]]):
# #     def __init__(self, env,
# #                  wrapper: Callable[[float], float],
# #                  episode_count: int,
# #                  step_count: int,
# #                  score_wrapper: Callable[[float], float] = lambda x: x):
# #         super().__init__()
# #         self.env = env
# #         self.wrapper = wrapper
# #         self.episode_count = episode_count
# #         self.step_count = step_count
# #         self.score_wrapper = score_wrapper

# #     def evaluate(self, s1: Program[float]) -> float:
# #         score = s1.evaluate_with_args(1, 4, 8, 16)
# #         return self.score_wrapper(score)

# #     @staticmethod
# #     def evaluate_episode(s1: Program[float],
# #                          env,
# #                          wrapper: Callable[[float], float],
# #                          episode_count: int,
# #                          step_count: int) -> float:
# #         score = 0.
# #         for i in range(0, episode_count):
# #             score = score + GymEvaluator.evaluate_step(s1, env, wrapper, step_count)
# #         return score / episode_count

# #     @staticmethod
# #     def evaluate_step(s1: Program[float],
# #                       env,
# #                       wrapper: Callable[[float], float],
# #                       step_count: int) -> float:
# #         step_result = env.reset()
# #         score = 0.
# #         # hard coded - an episode consists of 10 evaluations.
# #         for i in range(0, step_count):
# #             if (len(step_result) >= 5 and (step_result[2] or step_result[3])):
# #                 break
# #             step_result = env.step(wrapper(s1.evaluate_with_args(*step_result[0])))  # type: ignore
# #             if (step_result[2]):
# #                 break
# #             score = score + step_result[1]  # type: ignore
# #         return score


# from ..core.population import Population

# progf = ProgramFactory((1, 2, 0, add, sub, mul, div, sin, cos, mul, div, lim, avg), 1)

# # Declare and populate the population
# pops: Population[Program[float]] = Population()

# POP_SIZE = 20
# TREE_DEPTH = 2
# NODE_BUDGET = 5
# STEP_COUNT = 5

# for i in range(0, POP_SIZE):
#     pops.append(progf.build(NODE_BUDGET, TREE_DEPTH))

# from ..core import LinearController
# from ..core import Evaluator
# from ..core import Individual, Population
# from ..core import Elitist, SimpleSelector, NullSelector, TournamentSelector, NullEvaluator, NullVariator
# from ..core import Variator

# def weird_function(x):
#     return x * 2 + cos(x)

# support = tuple((x/50,) for x in range(-100, 100))

# eval = SymbolicEvaluator(objective=weird_function, support = support)

# pe = eval
# ps = Elitist(SimpleSelector(POP_SIZE))


# ts = TournamentSelector(POP_SIZE)

# var = ProgramCrossoverVariator()
# coer = SmallerIsBetter()

# ctrl = LinearController(parent_evaluator=NullEvaluator(),
#                         parent_selector=NullSelector(),
#                         population=pops,
#                         survivor_evaluator=pe,
#                         survivor_selector=ps,
#                         variator=var)

# print(f"{ctrl.population}")

# fitnesses = []
# for _ in range(STEP_COUNT):
#     ctrl.step()
#     # print(f"{ctrl.population}")
#     fitnesses.append(ctrl.population.best().fitness)
# print(f"{fitnesses}")

