from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
    from typing import Dict
    from typing import Any
    from typing import Callable
    from typing import Sequence
    from typing import Optional
    from typing import List
    from .controller import Controller

from typing import NamedTuple


class AccountantRecord(NamedTuple):
    #: Event that triggers the handler.
    event: str

    #: Generation count when the event is fired.
    generation: int

    #: Data that is collected by the handler.
    value: Any

class Accountant:
    """Monitor and collect data from a running :class:Controller.

    The `Accountant` maintains a dictionary of event:handler mappings. When
    an event fires in the attached :class:`.Controller`, the corresponding
    handler collects data.

    Attention:
        One `Accountant` can only be registered with one :class:`.Controller`;
        one :class:`.Controller` can have multiple `Accountant` s.
    """
    def __init__(self: Self, handlers: Dict[str, Callable[[Controller], Any]]):
        """
        Args:
            handlers: a dictionary of event:handler mappings. Each handler
                should receive a :class:`.Controller` and return a value.
        """
        self.records: List[AccountantRecord] = []
        #: Mapping between events and handlers
        self.handlers: Dict[str, Callable[[Controller], Any]] = handlers
        self.subject: Optional[Controller] = None

    def register(self: Self, subject: Controller) -> None:
        """Register with a :class:`.Controller`.

        Args:
            subject: the :class:`.Controller` whose events are monitored by
                this `Accountant`.
        """
        self.subject = subject

    def update(self: Self, event: str)-> None:
        """Machinery.
        
        The attached :class:`.Controller` calls this method
        to report an event.

        :meta private:
        """
        if self.subject == None:
            raise RuntimeError("Accountant updated without a subject.")
        else:
            for trigger, action in self.handlers.items():
                if event == trigger:
                    self.records.append(AccountantRecord(event,
                                                         self.subject.generation,
                                                         action(self.subject)))

    def publish(self)-> List[AccountantRecord]:
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
        if not self.is_attached():
            raise ValueError("Accountant is not attached to a controller;"
                             " cannot publish.")
        return self.records

    def is_attached(self)-> bool:
        """Return if this `Accountant` is attached to a :class:Controller.

        Returns:
            `True` if 
        """
        return self.subject is not None
