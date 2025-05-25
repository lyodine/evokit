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
    """Machinery. Implement special behavious in :class:`Controller`.

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
    """Base class for all evolutionary algorothms.

    Derive this class to create custom algorithms.
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

        The implementation can accept operators as arguments. Alternatively,
        it may also acquire operators from the global scope, or define them
        in the initialiser.
        """
        # TODO The note is just not right - normally, the child should
        #   call the initialiser of the parent/

        #: Generation counter, automatically increments wit :py:attr:`step`.
        self.generation: int
        #: Registered :class:`Accountant` objects.
        self.accountants: List[Accountant]
        #: Collection of events that can be reported by this controller.
        self.events: List[str]

    @abstractmethod
    def step(self) -> None:
        """Advance the population by one generation.

        Subclasses should override this method.

        Note:
            Do not manually increment :attr:`generation`. This property
            is automatically managed.
        """
        # TODO Should I use this note to make it clear?
        pass

    def register(self: Self, accountant: Accountant) -> None:
        """Attach an :class:`.Accountant` to this controller.

        Args:
            accountant: An :class:`.Accountant` that observes and
                collects data from this Controller.
        """
        self.accountants.append(accountant)
        accountant.subscribe(self)

    def update(self, event: str) -> None:
        """Report an event to all attached :class:`.Accountant` objects.

        The event must be in :attr:`events`. If not, raise an exception.

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


class SimpleLinearController(Controller):
    """A very simple evolutionary algorithm.

    An evolutionary algorithm that maintains one population and does not
    take advantage of parallelism. The algorithm applies its operators
    in the following order:

        #. **evaluate** for selection
        #. **selection**
        #. *update population*
        #. **vary** parents
        #. *update population*
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
        # wwerwe
        # """
        # Args:
        # TODO These names are repeated in the class docstring.
        #     population: initial population.

        #     parent_evaluator: operator that evaluate the fitness of an individual.

        #     parent_selector: operator that selects individuals for variation.

        #     variator: operator that creates new individuals from existing ones.

        #     survivor_evaluator: operator that selects to the next generation.

        #     survivor_selector: operator that selects to the next generation.
        # """

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
        # _Introduction to Evolutionary Computing_ calls
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
        # wwerwe
        # """
        # Args:
        # TODO These names are repeated in the class docstring.
        #     population: initial population.

        #     parent_evaluator: operator that evaluate the fitness of an individual.

        #     parent_selector: operator that selects individuals for variation.

        #     variator: operator that creates new individuals from existing ones.

        #     survivor_evaluator: operator that selects to the next generation.

        #     survivor_selector: operator that selects to the next generation.
        # """

    @override
    def step(self) -> None:
        self.parent_evaluator.evaluate_population(self.population)
        self.update("GENERATION_BEGIN")
        # Update the population after each event. This ensures that
        #   the :class:`Accountant` always has access to the most
        #   up-to-date information.
        # print(f"POP PE is {[x.fitness for x in self.population]}")
        self.population = \
            self.parent_selector.select_to_population(self.population)
        self.update("POST_PARENT_SELECTION")
        # print(f"POP PS is {[x.fitness for x in self.population]}")
        
        self.population = self.variator.vary_population(self.population)
        self.update("POST_VARIATION")
        # print(f"POP VAR is {[x.fitness for x in self.population]}")

        self.survivor_evaluator.evaluate_population(self.population)
        self.update("POST_SURVIVOR_EVALUATION")
        # print(f"POP SE is {[x.fitness for x in self.population]}")

        self.population = self.survivor_selector.select_to_population(self.population)
        self.update("POST_SURVIVOR_SELECTION")
        # print(f"POP SS is {[x.fitness for x in self.population]}")
