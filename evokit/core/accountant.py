from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from typing import Dict
    from typing import Any
    from typing import Callable
    from typing import Optional
    from typing import List
    from .controller import Controller

from typing import NamedTuple


class AccountantRecord(NamedTuple):
    """A value collected by an :class:`Accountant`, with the context
    in which it is collected.
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


class Accountant:
    """Monitor and collect data from a running :class:`Controller`.

    Maintain a dictionary of `event : handler` mappings. When
    `event` fires in the attached :class:`.Controller`,
    `handler` collects data.

    The accountant subscribes to a :class:`.Controller`,
    the :class:`.Controller` registers an accountant.
    """
    # TODO is this langauge good
    def __init__(self: Self, handlers: Dict[str, Callable[[Controller], Any]]):
        """
        Args:
            handlers: a dictionary of `event : handler` mappings. Each `handler`
                should have the following signature:

        .. code-block::

            Controller -> Any

        """
        self.records: List[AccountantRecord] = []
        # TODO I will skip on commenting it - the handler should not be
        #   directly accessed though ... should I make it possible to
        #   change the handlers once they are declared?
        # Meditating on how to do it.
        self.handlers: Dict[str, Callable[[Controller], Any]] = handlers

        #: The attached :class:`Controller`
        self.subject: Optional[Controller] = None

    def subscribe(self: Self, subject: Controller) -> None:
        """Machinery.

        Subscribe for events in a :class:`.Controller`.

        Args:
            subject: the :class:`.Controller` whose events are monitored by
                this accountant.

        :meta private:
        """
        self.subject = subject

    def update(self: Self, event: str) -> None:
        """Machinery.

        When the attached :class:`.Controller` calls :meth:`.Controller.update`,
        it calls this method on every registered accountant.

        When an event matches a key in :attr:`handlers`, call the corresponding
        value with the attached Controller as argument. Store the result in
        :attr:`records`.

        Raise:
            RuntimeError: If no :class:`Controller` is attached.

        :meta private:
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
        # Bad comment!
        """Report collected data.

        Each time an event fires in the attached :class`.Controller`,
        if that event is registered in :attr:`handlers`, then the
        return value of the corresponding handler adds to this list,
        alongside the context in which the value is returned.

        Returns:
            A list of named tuples. See :class:`.AccountantRecord` for fields of
            each item.
        """
        if not self.is_registered():
            raise ValueError("Accountant is not attached to a controller;"
                             " cannot publish.")
        return self.records

    def is_registered(self) -> bool:
        """Return if this accountant is attached to a :class:Controller.

        Returns:
            `False` if :attr:`subject` is `None`, otherwise `True`.
        """
        return self.subject is not None
