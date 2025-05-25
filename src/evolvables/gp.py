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

import abc
import functools
import math
import random
import typing
from inspect import signature
from random import choice
from typing import Generic

import gymnasium as gym

from core import (Controller, Elitist, Evaluator, Individual, Population,
                  SimpleSelector, Variator)

T = typing.TypeVar("T")

class ArityMismatch(TypeError):
    def __init__(self, expr, expected:Optional[int], given: Optional[int]):
        super().__init__(f"function {str(expr)} expects "
                         f"{expected} arguments, got"
                         f"{given}.")

def _get_arity(fun: Any) -> int:
    """Inspect the arity of an object

    Return the signatue length of a callable. If the input is not callable,
        return 0.
    
    Args:
        fun: An object

    Return:
        The arity of `fun`
    """
    if (callable(fun)):
        return len(signature(fun).parameters)                 
    elif isinstance(fun, Program):
        # Specialised code for programs
        return len(fun.symbols)
    else:
        return 0

class Expression(abc.ABC, typing.Generic[T]):
    def __init__(self, function: T | typing.Callable[..., T], *children: Expression[T]):
        self._function = function
        self.children : List[Expression[T]] = list(children)
    
    def evaluate(self) -> T:
        expected_arity = _get_arity(self._function)
        children_arity = len(self.children)
        results = tuple(x.evaluate() for x in self.children)
        if callable(self._function):
            if (expected_arity == children_arity):
                return self._function(*results)
            else:
                raise ArityMismatch(self._function, expected_arity, children_arity)
        elif expected_arity == 0 and children_arity == 0:
            return self._function
        else:
            raise ArityMismatch(self._function, expected_arity, children_arity)
        
        return self._function(*results)
    
    def copy(self) -> Self:
        """ Copying self does not copy the funciton. """
        children_copies : Tuple[Expression[T], ...] = tuple(x.copy() for x in self.children)
        return self.__class__(self._function, *children_copies)
    
    def nodes(self) -> List[Expression[T]]:
        return [self] + list(self.children)
    
    def __str__(self) -> str:
        delimiter = ", "

        my_name: str = self._function.__name__ if callable(self._function) else str(self._function)

        children_name: str
        if len(self.children) < 1:
            children_name = ""
        else:
            children_name = f"({functools.reduce(lambda x, y: str(x) + ", " + str(y), [str(x) for x in self.children])})"
        
        
        return (f"{my_name}{children_name}")
    

    __copy__ = copy
    __deepcopy__ = copy


class ExpressionFactory(typing.Generic[T]):
    def __init__(self, functions: Tuple[Callable[..., T], ...]):
        # Build a pool of functions, as a dictionary where each index corresponds to an arity, and each 
        #   value is a list of functions (or terminals!) with that arity.
        self.function_pool: Dict[int, List[Callable[..., T]]] = {}
        for fun in functions:
            arity: int = _get_arity(fun)
            if arity in self.function_pool:
                self.function_pool[arity].append(fun)
            else:
                self.function_pool[arity] = [fun]

        self.depth_cap: int = 0
        self.budget_cap: int = 0
        self.depth = 0
        self.budget_used = 0

    def build(self, depth: int, budget: int, nullary_ratio: Optional[float] = None) -> Expression:
        self.budget_cap = budget
        self.budget_used = 0

        target_function = self.poll_function(nullary_ratio)
        arity = _get_arity(target_function)

        children : List [Expression]= []
        for i in range(0, arity):
            children.append(self._build_recurse(depth-1, nullary_ratio))

        root = Expression(target_function, *children)
        return root
        

    def _build_recurse(self, depth_left: int, nullary_ratio: Optional[float] = None) -> Expression:
        if (depth_left < 1 or self.over_budget()):
            target_function = self.poll_arity(0)
            return Expression(target_function)
        else:
            
            target_function = self.poll_function(nullary_ratio)
            arity = _get_arity(target_function)
            children : List [Expression]= []
            for i in range(0, arity):
                children.append(self._build_recurse(depth_left-1, nullary_ratio))
            random.shuffle (children)
            base = Expression[T](target_function, *children)
            return base

    def over_budget(self) -> bool:
        return self.budget_used > self.budget_cap

    def cost_budget(self) -> None:
        self.budget_used = self.budget_used + 1
        # report(LogLevel.TRC, f"budget used: {self.budget_used - 1} -> {self.budget_used}")
    
    def poll_function(self, nullary_ratio:Optional[float] = None) -> Callable[..., T]:
        self.cost_budget()
        choice_poll: List[Callable[..., T]]
        if (nullary_ratio is None):
            choice_poll = choice(list(self.function_pool.values()))
        else:
            if (random.random() < nullary_ratio):
                choice_poll = self.function_pool[0]
            else:
                choice_poll = choice([self.function_pool[x] for x in self.function_pool.keys() if x != 0])            
            
        choice_function: Callable[..., T] = choice(choice_poll)

        return choice_function

    def poll_arity(self, arity: int) -> Callable[..., T]:
        return choice(self.function_pool[arity])

class BadSymbolError(Exception):
    def __init__(self, name: str):
        super().__init__(f"The symbol {name} is used but not assigned.")


class Symbol(typing.Generic[T]):
    def __init__(self, name: str = "default_symbol_name", value: Optional[T] = None):
        self.value : Optional[T] = value
        self.__name__ : str = name

    def __call__(self) -> T:
        if (self.value is None):
            raise BadSymbolError(self.__name__)
        return self.value
    
    def assign(self, val: T) -> None:
        self.value = val
    
    def __str__(self)-> str:
        return self.__name__

class ProgramFactory(Generic[T]):
    def __init__(self, functions: Tuple[Callable[..., T], ...], arity):
        self.arity = arity
        self._symbol_count = 0 # only used to keep track of symbol names. Does not relate to arity
        self.symbol_deposit : List[Symbol]= []
        
        for i in range(0, arity):
            self.deposit_symbol(self.next_symbol())

        self.exprfactory = ExpressionFactory[T](functions + tuple(self.symbol_deposit))

    def next_symbol_name(self) -> str:
        self._symbol_count = self._symbol_count + 1
        return str(self._symbol_count)

    def deposit_symbol(self, s: Symbol[T]) -> None:
        self.symbol_deposit.append(s)
        
    def next_symbol(self) -> Symbol[T]:
        return Symbol("sym_" + self.next_symbol_name())
    
    def build(self, depth: int, budget: int, unary_weight: Optional[float] = None) -> Program:
        return Program(self.exprfactory.build(depth, budget, unary_weight), self.symbol_deposit, self)

# Note that programs from the same factory share the same set of argument values.
# This should be desirable - and well hidden - if the object is only shared by one thread.
# I'm not prepared to deal with concurrency.

class ProgramArityMismatchError(Exception):
    def __init__(self, expected:Optional[int], given: Optional[int]):
        super().__init__(f"The program is expecting {expected} arguments, only {given} are given.")
        
class Program(Individual[T]):
    """
    
    """
    def __init__(self, expr: Expression, symbols: List[Symbol], factory: ProgramFactory):
        super().__init__()
        self.expr = expr
        self.symbols = symbols
        self.factory = factory
    
    def evaluate(self, *args: T) -> T:
        if (len(args) != len(self.symbols)):
            raise ProgramArityMismatchError(len(self.symbols), len(args))
        self.__class__._assign_values(self.symbols, args)
        return self.expr.evaluate()
    
    def __call__(self, *args: T) -> T:
        return self.evaluate(*args)

    @staticmethod
    def _assign_values(symbols: List[Symbol[T]], values: Tuple[T, ...]) -> None:
        # This is exceptionally unpythonic
        for i in range (0, len(symbols)):
            symbols[i].assign(values[i])

    def __str__(self) -> str:
        return str(self.expr)
    
    # Warning! Breaking design patterns.
    def nodes(self) -> List[Expression[T]]:
        return self.expr.nodes()
    
    def copy(self) -> Self:
        return self.__class__(self.expr.copy(), self.symbols, self.factory)

def sin(x: float) -> float:
    return math.sin(x)

def cos(x: float) -> float:
    return math.cos(x)

def tan(x: float) -> float:
    return math.tan(x)

def add (x:float, y:float):
    return x + y

def sub (x:float, y:float):
    return x - y

def mul (x:float, y:float):
    return x * y

def div (x:float, y:float):
    if y == 0:
        return 1
    return x / y

def avg (x:float, y:float):
    return (x+y)/2

def lim(x: float, max_val:float, min_val:float) -> float:
    return max(min(max_val, x), min_val)

class ProgramCrossoverVariator(Variator[Program[float]]):
    def vary(self, parents: Tuple[Program[float], ...]) -> Tuple[Program[float], ...]:
        return (self.crossover(parents) + self.mutate(parents))

    def crossover(self, parents: Tuple[Program[float], ...]) -> Tuple[Program[float], ...]:
        root1: Program = parents[0].copy()
        root2: Program = parents[1].copy()

        expression_nodes_from_root_1 = root1.nodes()
        expression_nodes_from_root_2 = root2.nodes()

        # Select internal nodes - nodes that receive arguments.
        expression_internal_nodes_from_root_1 = [x for x in expression_nodes_from_root_1 if len(x.children) > 0]
        expression_internal_nodes_from_root_2 = [x for x in expression_nodes_from_root_2 if len(x.children) > 0]

        # If both expression trees have valid internal nodes, 
        if (len(expression_internal_nodes_from_root_1) >= 1 and len(expression_internal_nodes_from_root_2) >= 1):
            expression_node_from_root_1_to_swap = random.choice(expression_internal_nodes_from_root_1)
            expression_node_from_root_2_to_swap = random.choice(expression_internal_nodes_from_root_2)
            self.__class__.swap_children(expression_node_from_root_1_to_swap, expression_node_from_root_2_to_swap)
        print (str(root1) + "-----" + str(root2))
        return (root1, root2)
    
    def mutate(self, parents: Tuple[Program[float], ...]) -> Tuple[Program[float], ...]:
        root: Program = parents[0].copy()
        root.expr._function = self.__class__._draw_replacement_function(root)
        return (tuple([root]))

    @staticmethod
    def swap_children(expr1: Expression[float], expr2: Expression[float]) -> None:
        child_nodes = list(expr1.children + expr2.children)
        random.shuffle(child_nodes)

        for i in range(0,len(expr1.children)):
            expr1.children[i] = child_nodes[i].copy()

        for i in range(-1,-(len(expr2.children) + 1), -1):
            expr2.children[i] = child_nodes[i].copy()

    @staticmethod
    def _draw_replacement_function(program: Program)-> Callable:
        source_factory = program.factory
        arity = _get_arity(program.expr._function)
        functions = source_factory.exprfactory.function_pool[arity]
        return random.choice(functions)




class SymbolicEvaluator(Evaluator[Program[float]]):
    def __init__(self, objective: Callable, support: Tuple[Tuple[float, ...], ...]):
        self.objective = objective
        self.support = support
        self.arity = _get_arity(objective)
        if self.arity != len(support[0]):
            raise TypeError("aaaaaaah")

    def evaluate(self, program: Program[float]) -> float:
        if self.arity != _get_arity(program):
            raise TypeError("what")
        return -sum([abs(self.objective(*sup) - program(*sup)) for sup in self.support])

class GymEvaluator(Evaluator[Program[float]]):
    def __init__(self, env, wrapper: Callable[[float], float], episode_count: int, step_count: int, score_wrapper: Callable[[float], float] = lambda x : x):
        super().__init__()
        self.env = env
        self.wrapper = wrapper
        self.episode_count = episode_count
        self.step_count = step_count
        self.score_wrapper = score_wrapper

    def evaluate(self, s1: Program[float]) -> float:
        score = s1.evaluate(1,4,8,16)
        #score = GymEvaluator.evaluate_episode(s1, self.env, self.wrapper, self.episode_count, self.step_count) 
        return self.score_wrapper(score)

    @staticmethod
    def evaluate_episode(s1: Program[float], env, wrapper: Callable[[float], float], episode_count: int, step_count: int) -> float:
        score = 0.
        for i in range(0, episode_count):
            score = score + GymEvaluator.evaluate_step(s1, env, wrapper, step_count)
        return score / episode_count

    @staticmethod
    def evaluate_step(s1: Program[float], env, wrapper: Callable[[float], float], step_count: int) -> float:
        step_result = env.reset()
        score = 0.
        # hard coded - an episode consists of 10 evaluations.
        for i in range(0, step_count):
            if (len(step_result)>=5 and (step_result[2] or step_result[3])):
                break
            step_result = env.step(wrapper(s1.evaluate(*step_result[0]))) #type: ignore
            if (step_result[2]):
                break
            score = score + step_result[1] #type: ignore
        return score


