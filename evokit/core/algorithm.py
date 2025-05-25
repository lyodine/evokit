from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from functools import wraps

if TYPE_CHECKING:
    from typing import Self
    from typing import Any
    from typing import Type
    from typing import Callable
    from ..accounting.accountant import Accountant

from typing import TypeVar
from typing import Generic

from .population import Individual


class _MetaAlgorithm(ABCMeta):
    """Machinery.

    :meta private:

    Implement special behaviours in :class:`Algorithm`:

        * After step is called, :attr:`.Algorithm.generation`
          increments by ``1``.
        * Fire event "STEP_BEGIN" before calling :meth:`.Algorithm.step`,
          fire event "STEP_END" after calling :meth:`.Algorithm.step`.
    """
    def __new__(mcls: Type[Any], name: str, bases: tuple[type],
                namespace: dict[str, Any]) -> Any:
        ABCMeta.__init__(mcls, name, bases, namespace)

        def wrap_step(custom_step: Callable) -> Callable:
            @wraps(custom_step)
            # The `@wraps` decorator ensures that the wrapper correctly
            #   inherits properties of the wrapped function, including
            #   docstring and signature.
            # Return type is None, because `wrapper` returns
            #   the output of the wrapped function: :meth:`step` returns None.
            def wrapper(*args: Any, **kwargs: Any) -> None:
                self = args[0]
                self.update("STEP_BEGIN")
                custom_step(*args, **kwargs)
                self.update("STEP_END")
                self.generation += 1

            return wrapper

        namespace["step"] = wrap_step(
            namespace.setdefault("step", lambda: None)
        )

        return type.__new__(mcls, name, bases, namespace)


T = TypeVar("T", bound=Individual)


class Algorithm(ABC, Generic[T], metaclass=_MetaAlgorithm):
    """Base class for all evolutionary algorithms.

    Derive this class to create custom algorithms.

    Tutorial: :doc:`../guides/examples/algorithm`.
    """
    def __new__(cls, *_: Any, **__: Any) -> Self:
        """Machinery.

        :meta private:

        Implement managed attributes.
        """
        # Note that Sphinx does not collect these values.
        #   It is therefore necessary to repeat them in :meth:`__init__`.
        instance = super().__new__(cls)
        instance.generation = 0
        instance.automatic_events = ["STEP_BEGIN", "STEP_END"]
        instance.accountants = []
        instance.events = []
        return instance

    @abstractmethod
    def __init__(self) -> None:
        """
        Subclasses should override this method.

        Initialise the state of an algorithm, including operators,
        the initial population(s), truncation strategy, and other
        parameters associated with the learning process as a whole.
        """

        #! Number of elapsed generations.
        self.generation: int
        #! Registered :class:`Accountant` objects.
        self.accountants: list[Accountant]
        #! Events that can be reported by this algorithm.
        self.events: list[str]
        #! Events that are automatically fired.
        self.automatic_events: list[str]

    @abstractmethod
    def step(self) -> None:
        """Advance the population by one generation.

        Subclasses should override this method. Use operators to update
        the population (or populations). Call :meth:`update` to fire
        events for data collection mechanisms such as :class:`Accountant`.

        Note:
            The :attr:`.generation` attribute increments by 1 _after_
            :meth:`.step` is called. Do not manually increment
            :attr:`generation`. This property is automatically managed.

            Calling :meth:`.step` automatically fires two events via
            :meth:`.update`: "STEP_BEGIN" before and "STEP_END" after.
            This behaviour cannot be suppressed. For more on events,
            see :class:`accounting.accountant.Accountant`.
        """
        pass

    def register(self: Self, accountant: Accountant) -> None:
        """Attach an :class:`.Accountant` to this algorithm.

        Args:
            accountant: An :class:`.Accountant` that observes and
                collects data from this Algorithm.
        """
        self.accountants.append(accountant)
        accountant._subscribe(self)

    def update(self, event: str) -> None:
        """Report an event to all attached :class:`.Accountant` objects.

        If the event is not in :attr:`events`, raise an exception.

        Args:
            event: The event to report.

        Raise:
            ValueError: if an reported event is not declared in
            :attr:`events` and is not an automatically reported
            event in :attr:`automatic_events`.
        """
        if event not in self.events and event not in self.automatic_events:
            raise ValueError(f"Algorithm fires unregistered event {event}."
                             f"Add {event} to the algorithm's list of"
                             "`.events`.")
        for acc in self.accountants:
            acc._update(event)
