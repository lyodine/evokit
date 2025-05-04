""" The controller is an iterative optimizer that receives various
    evolutionary operators.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from functools import wraps

if TYPE_CHECKING:
    from typing import Self
    from typing import List
    from typing import Any
    from typing import Dict
    from typing import Tuple
    from typing import Type
    from typing import Callable
    from .evaluator import Evaluator
    from .variator import Variator
    from .selector import Selector
    from .population import Population
    from .accountant import Accountant

from typing import Generic, TypeVar
from typing import override

from .population import Individual

T = TypeVar("T", bound=Individual)


class MetaController(ABCMeta):
    """Machinery. Implement special behavious in :class:`Controller`.

    :meta private:
    """
    def __new__(mcls: Type, name: str, bases: Tuple[type],
                namespace: Dict[str, Any]) -> Type:
        ABCMeta.__init__(mcls, name, bases, namespace)
        def wrap_step(custom_step: Callable) -> Callable:
            @wraps(custom_step)
            # The `@wraps` decorator ensures that the wrapper correctly
            #   inherits properties of the wrapped function, including
            #   docstring and signature.
            # Return type is Any, because `wrapper` returns
            #   the output of the wrapped function.
            def wrapper(*args, **kwargs) -> Any:
                self = args[0]
                self.generation += 1
                return custom_step(*args, **kwargs)

            return wrapper

        namespace["step"] = wrap_step(
            namespace.setdefault("step", lambda: None)
        )

        def wrap_init(custom_init: Callable) -> Callable:
            def wrapper(self: Controller, *args, **kwargs) -> Any:
                self.generation = 0
                self.accountants = []
                self.events = []
                return custom_init(self, *args, **kwargs)

            return wrapper
        namespace["__init__"] = wrap_init(
            namespace.setdefault("__init__", lambda: None)
        )
        return type.__new__(mcls, name, bases, namespace)


class Controller(ABC, Generic[T], metaclass=MetaController):
    """Base class for all evolutionary algorothms.

    The `Controller` Manage the learning process. Derive this class to create custom algorithms.
    """
    def __new__(cls, *args, **kwargs):
        """Machinery. Implement managed attributes.

        :meta private:
        """
        # Note that Sphinx does not collect these values.
        #   It is therefore necessary to repeat them in :meth:`__init__`.
        instance = super().__new__(cls)
        instance.generation = 0
        instance.accountants = []
        instance.events = []
        return instance

    @abstractmethod
    def __init__(self) -> None:
        """
        Args:
            events: Collection of events that can be fired by the controller.

        Note:
            No need to not call super().init(...) when overriding :func:`__init__`.
            The attributes :attr:`generation`, :attr:`accountants`,
            and :attr:`events` are automatically managed.
        """
        # TODO The note is just not right - normally, the child should call the initialiser of the parent/
        
        #: Generation counter, automatically increments when :py:attr:`step` is called.
        self.generation: int
        #: Registered :class:`Controller` s.
        self.accountants: List[Accountant]
        #: Events that can be fired by this Controller.
        self.events: List[str]

    @abstractmethod
    def step(self) -> Self:
        """Advance the population by one generation.

        Update the current population or populations. Incrementing of
        the :attr:`generation` counter is automatically managed.
        """
        # TODO Calling super.step() may lead to unforseen consequences, such as
        #   incrementing the generation counter twice. Just override it.
        # Try to prevent this.
        pass

    def register(self: Self, accountant: Accountant)-> None:
        """Attach an :class:`.Accountant` to this `Controller`.

        Args:
            accountant: An :class:`.Accountant` that observes and
                collects data from this `Controller`.
        """
        # TODO I just can't come up with a good name
        self.accountants.append(accountant)
        accountant.subscribe(self)

    def update(self, event: str) -> None:
        """Report an event to all attached :class:`.Accountant` s.

        The event must be one listed in :attr:`events`. If not, raise
        an exception.

        Args:
            event: the event to report.

        Raise:
            ValueError: if an reported event is not registered.
        """
        if event not in self.events:
            raise ValueError(f"Controller fires unregistered event {event}."
                             f"Add {event} to the controller's .events value")
        for acc in self.accountants:
            acc.update(event)


class LinearController(Controller[T]):
    """A simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. The algorithm applies its operators
    in the following order:

        #. **evaluate** for parent selection
        #. parent **selection**
        #. *update population*
        #. **vary** parents
        #. **evaluate** for survivor selection
        #. survivor **selection**
        #. *update population*
    """
    @override
    def __init__(self,
                 population: Population[T],
                 parent_evaluator: Evaluator[T],
                 parent_selector: Selector[T],
                 variator: Variator[T],
                 survivor_evaluator: Evaluator[T],
                 survivor_selector: Selector[T]) -> None:
        """
        Args:
            population: initial population.

            evaluator: operator that evaluate the fitness of an individual.

            parent_selector: operator that selects individuals for variation.

            variator: operator that creates new individuals from existing ones.

            offspring_selector: operator that selects to the next generation.
        """
        # Introduction to Evolutionary Computing calls
        #   selectors "survivor selection" and the outcome
        #   "offspring". I'm not making the call there.
        self.population = population
        self.parent_evaluator = parent_evaluator
        self.parent_selector = parent_selector
        self.variator = variator
        self.survivor_evaluator = survivor_evaluator
        self.survivor_selector = survivor_selector
        self.accountants: List[Accountant] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".
        self.events: List[str] = ["GENERATION_BEGIN",
                                  "POST_PARENT_SELECTION",
                                  "POST_VARIATION",
                                  "POST_SURVIVOR_EVALUATION",
                                  "POST_SURVIVOR_SELECTION"]

    @override
    def step(self) -> None:
        self.parent_evaluator.evaluate_population(self.population)
        self.update("GENERATION_BEGIN")
        # Update the population after each event. This ensures that
        #   the :class:`Accountant` always has access to the most
        #   up-to-date information.
        self.population = \
            self.parent_selector.select_to_population(self.population)
        self.update("POST_PARENT_SELECTION")

        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.survivor_evaluator.evaluate_population(self.population)
        self.update("POST_SURVIVOR_EVALUATION")
        
        self.population = self.survivor_selector.select_to_population(self.population)
        self.update("POST_SURVIVOR_SELECTION")
