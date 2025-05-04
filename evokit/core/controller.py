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

from typing import TypeVar
from typing import override

from .population import Individual

T = TypeVar("T", bound=Individual)


class MetaController(ABCMeta):
    """Machinery. Implement special behaviours in :class:`Controller`.

    :meta private:
    """
    def __new__(mcls: Type[Any], name: str, bases: Tuple[type],
                namespace: Dict[str, Any]) -> Any:
        ABCMeta.__init__(mcls, name, bases, namespace)

        def wrap_step(custom_step: Callable) -> Callable:
            @wraps(custom_step)
            # The `@wraps` decorator ensures that the wrapper correctly
            #   inherits properties of the wrapped function, including
            #   docstring and signature.
            # Return type is Any, because `wrapper` returns
            #   the output of the wrapped function.
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self = args[0]
                self.generation += 1
                return custom_step(*args, **kwargs)

            return wrapper

        namespace["step"] = wrap_step(
            namespace.setdefault("step", lambda: None)
        )

        return type.__new__(mcls, name, bases, namespace)


class Controller(ABC, metaclass=MetaController):
    """Base class for all evolutionary algorithms.

    Derive this class to create custom algorithms.

    Tutorial: :doc:`../guides/examples/controller`.
    """
    def __new__(cls, *_: Any, **__: Any) -> Self:
        """Machinery.

        Implement managed attributes.
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
        Subclasses should override this method.

        The initialiser should create (or accept as argument) operators used
        in the algorithm.
        """
        # TODO The note is just not right - normally, the child should
        #   call the initialiser of the parent/

        #: Generation counter, automatically increments wit :py:attr:`step`.
        self.generation: int
        #: Registered :class:`Accountant` objects.
        self.accountants: List[Accountant]
        #: Events that can be reported by this controller.
        self.events: List[str]

    @abstractmethod
    def step(self) -> None:
        """Advance the population by one generation.

        Subclasses should override this method. Use operators to update
        the population (or populations). Call :meth:`update` to fire events.

        Example:

        .. code-block:: Python

            self.population = self.variator.vary_population(self.population)
            self.update("POST_VARIATION")

            self.evaluator.evaluate_population(self.population)
            self.update("POST_EVALUATION")

            self.population = \\
                self.selector.select_to_population(self.population)

        Note:
            Do not manually increment :attr:`generation`. This property
            is automatically managed.
        """
        pass

    def register(self: Self, accountant: Accountant) -> None:
        """Attach an :class:`.Accountant` to this controller.

        Args:
            accountant: An :class:`.Accountant` that observes and
                collects data from this Controller.
        """
        self.accountants.append(accountant)
        accountant._subscribe(self)

    def update(self, event: str) -> None:
        """Report an event to all attached :class:`.Accountant` objects.

        If the event is not in :attr:`events`, raise an exception.

        Args:
            event: The event to report.

        Raise:
            ValueError: if an reported event is not registered.
        """
        if event not in self.events:
            raise ValueError(f"Controller fires unregistered event {event}."
                             f"Add {event} to the controller's .events value")
        for acc in self.accountants:
            acc._update(event)


class SimpleLinearController(Controller):
    """A very simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. The algorithm applies its operators
    in the following order:

        #. fire event ``GENERATION_BEGIN``
        #. **evaluate** for selection
        #. fire event ``POST_VARIATION``
        #. select for **survivors**
        #. update :attr:`population`
        #. fire event ``POST_EVALUATION``
        #. **vary** parents
        #. update :attr:`population`
        #. fire event ``POST_SELECTION``
    """
    @override
    def __init__(self,
                 population: Population[T],
                 evaluator: Evaluator[T],
                 selector: Selector[T],
                 variator: Variator[T]) -> None:
        self.population = population
        self.evaluator = evaluator
        self.selector = selector
        self.variator = variator
        self.accountants: List[Accountant] = []
        # Each event name informs what action has taken place.
        #   This should be easier to understand, compared to "PRE_...".
        self.events: List[str] = ["GENERATION_BEGIN",
                                  "POST_VARIATION",
                                  "POST_EVALUATION",
                                  "POST_SELECTION"]

    @override
    def step(self) -> None:
        self.update("GENERATION_BEGIN")

        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")

        self.evaluator.evaluate_population(self.population)
        self.update("POST_EVALUATION")

        self.population = \
            self.selector.select_to_population(self.population)
        self.update("POST_SELECTION")


class LinearController(Controller):
    """A simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. The algorithm applies its operators
    in the following order:

        #. fire event ``"GENERATION_BEGIN"``
        #. **evaluate** for parent selection
        #. fire event ``POST_PARENT_EVALUATION``
        #. select for **parents**
        #. update :attr:`population`
        #. fire event ``POST_PARENT_SELECTION``
        #. **vary** parents
        #. fire event ``POST_VARIATION``
        #. **evaluate** for survivor selection
        #. fire event ``POST_SURVIVOR_EVALUATION``
        #. select for **survivors**
        #. update :attr:`population`
        #. fire event ``POST_SURVIVOR_SELECTION``
    """
    @override
    def __init__(self,
                 population: Population[T],
                 parent_evaluator: Evaluator[T],
                 parent_selector: Selector[T],
                 variator: Variator[T],
                 survivor_evaluator: Evaluator[T],
                 survivor_selector: Selector[T]) -> None:
        # _Introduction to Evolutionary Computing_ calls
        #   selectors "survivor selection" and the outcome
        #   "offspring". These terms are taken from that book.
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
                                  "POST_PARENT_EVALUATION",
                                  "POST_PARENT_SELECTION",
                                  "POST_VARIATION",
                                  "POST_SURVIVOR_EVALUATION",
                                  "POST_SURVIVOR_SELECTION"]

    @override
    def step(self) -> None:
        self.update("GENERATION_BEGIN")
        self.parent_evaluator.evaluate_population(self.population)
        self.update("POST_PARENT_EVALUATION")
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
