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
    generation: int
    event: str
    value: Any

class Accountant:
    """
    The accountant should avoid triggering events in the controller.
    Otherwise, the event may update the accountant, which triggers another event,
        and so on.
    """
    def __init__(self: Self, handlers: Dict[str, Callable[[Controller], Any]]):
        self.records: List[AccountantRecord] = []
        self.handlers: Dict[str, Callable[[Controller], Any]] = handlers
        self.subject: Optional[Controller] = None

    def register(self: Self, subject: Controller)-> None:
        self.subject = subject

    def update(self: Self, event: str)-> None:
        if self.subject == None:
            raise ValueError("This accountant is updated without an attached controller; this should not happen")
        else:
            for trigger, action in self.handlers.items():
                if event == trigger:
                    self.records.append(AccountantRecord(self.subject.generation, event, action(self.subject)))

    def publish(self)-> Sequence[AccountantRecord]:
        if not self.attached:
            raise ValueError("Accountant is not attached to a controller; cannot publish")
        return self.records
    
    @property
    def attached(self)-> bool:
        return self.subject is not None
