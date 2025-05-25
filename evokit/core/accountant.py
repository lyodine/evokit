from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from typing import Dict
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import List

from typing import Generic
from .controller import Controller
from typing import TypeVar
from typing import NamedTuple

C = TypeVar("C", bound=Controller)


class AccountantRecord(NamedTuple, Generic[C]):
    """A value collected by an :class:`Accountant`; also contains the context
    in which that value is collected.
    """
    # TODO Sphinx somehow collects `__new__`, which should not be documented.
    # Spent 1 hour on this to no avail, will leave it be for the interest
    #   of time.

    #: Event that triggers the handler.
    event: str

    #: Generation count when the event :attr:`event` occurs.
    generation: int

    #: Data collected in generation :attr:`generation` after event :attr:`event`.
    value: Any


class Accountant(Generic[C]):
    """Monitor and collect data from a running :class:`Controller`.

    Maintain a dictionary of `event : handler` mappings. Each time
    `event` fires, `handler` collects data from the :class:`Controller`.

    Call :meth:`.Controller.register` to register an ``Accountant`` to
    a :class:`Controller`.

    Example:

    .. code-block:: python

        ctrl = SimpleLinearController(...)
        acc1 = Accountant(handlers={"POST_EVALUATION":
                                    lambda x: len(x.population)})
        ctrl.register(acc1)

        for _ in range(...):
            ctrl.step()

        report = acc1.publish()

    Tutorial: :doc:`../guides/examples/accountant`.

    """
    def __init__(self: Self, handlers: Dict[str, Callable[[C], Any]]):
        """
        Args:
            handlers: a dictionary of `event : handler` mappings. Each `handler`
                should have the signature :python:`Controller -> Any`:
        """
        #: Records collected by the ``Accountant``
        self.records: List[AccountantRecord] = []

        #: `Event - handler` pairs of the ``Accountant``
        self.handlers: Dict[str, Callable[[C], Any]] = handlers

        #: The attached :class:`Controller`
        self.subject: Optional[C] = None

    def _subscribe(self: Self, subject: C) -> None:
        """Machinery.

        Subscribe for events in a :class:`.Controller`.

        Args:
            subject: the :class:`.Controller` whose events are monitored by
                this accountant.
        """
        self.subject = subject

    def _update(self: Self, event: str) -> None:
        """Machinery.

        When the attached :class:`.Controller` calls :meth:`.Controller.update`,
        it calls this method on every registered accountant.

        When an event matches a key in :attr:`handlers`, call the corresponding
        value with the attached Controller as argument. Store the result in
        :attr:`records`.

        Raise:
            RuntimeError: If no :class:`Controller` is attached.
        """
        if self.subject is None:
            raise RuntimeError("Accountant updated without a subject.")
        else:
            for trigger, action in self.handlers.items():
                if event == trigger:
                    self.records.append(AccountantRecord(event,
                                                         self.subject.generation,
                                                         action(self.subject)))

    def publish(self) -> List[AccountantRecord]:
        """Report collected data.

        Each time an event fires in the attached :class`.Controller`,
        if that event is registered in :attr:`handlers`, supply the
        :class`.Controller` to the handler as argument then collect
        the result in an :class:`AccountantRecord`. This method
        returns a list of all collected records.
        """
        if not self.is_registered():
            raise ValueError("Accountant is not attached to a controller;"
                             " cannot publish.")
        return self.records

    def is_registered(self) -> bool:
        """Return if this accountant is attached to a :class:Controller.
        """
        return self.subject is not None
