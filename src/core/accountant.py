from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self
    from typing import Dict
    from typing import Any
    from typing import Callable
    from typing import Sequence
    from .controller import Controller

from .controller import ControllerEvent

from typing import NamedTuple

class AccountantRecord(NamedTuple):
    generation: int
    event: ControllerEvent
    value: Any

class Accountant:
    """
    The accountant should avoid triggering events in the controller.
    Otherwise, the event may update the accountant, which triggers another event,
        and so on.
    """
    def __init__(self: Self, handlers: Dict[ControllerEvent, Callable[[Controller], Any]]):
        self.records = []
        self.handlers = handlers
        self.subject = None

    def register(self: Self, subject: Controller):
        self.subject = subject

    def update(self: Self, event: ControllerEvent):
        for trigger, action in self.handlers.items():
            if event == trigger:
                self.records.append(AccountantRecord(1, event, action(self.subject)))

    def publish(self)-> Sequence[AccountantRecord]:
        if not self.attached:
            raise ValueError("Accountant is not attached to a controller; cannot publish")
        return self.records
    
    @property
    def attached(self):
        return self.subject is not None