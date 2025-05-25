from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Generic
from ..core.algorithm import Algorithm
from typing import TypeVar
from typing import NamedTuple
from typing import override, overload

import time

if TYPE_CHECKING:
    from typing import Self
    from typing import Any
    from typing import Callable
    from typing import Optional
    from collections.abc import Container

from typing import Sequence
C = TypeVar("C", bound=Algorithm)

T = TypeVar("T")


class AccountantRecord(NamedTuple, Generic[T]):
    """A value collected by an :class:`Accountant`; also contains the context
    in which that value is collected.

    AccountantRecord

    Warn:
        Attributes of an :class:`AccountantRecord` can be changed.
        Because the :meth:`.Accountant` reports the same record that
        it stores, changing attributes of its record will affect
        all future reports by the accountant.
    """
    # TODO Sphinx somehow collects `__new__`, which should not be documented.
    # Spent 1 hour on this to no avail, will leave it be for the interest
    #   of time.

    #: Event that triggers the handler.
    event: str

    #: Generation count when the event :attr:`event` occurs.
    generation: int

    #: Data collected in :attr:`generation` after :attr:`event`.
    value: T

    #: Time when the event :attr:`event` occurs.
    time: float = time.process_time()


class Accountant(Generic[C, T], Sequence[AccountantRecord[T]]):
    """Monitor and collect data from a running :class:`Algorithm`.
    Each event handler is recorded as an `event : callable` pair:
    when the `event` fires, the `handler` collects data from
    the algorithm.

    Call :meth:`.Algorithm.register` to register an :class:`Accountant` to
    a :class:`Algorithm`. Collected data can be retrieved as a sequence of
    :class:`AccountantRecord` s.

    For type checking, the :class:`Accountant` has two
    type parameter ``C`` and ``T``. ``C`` is the type of the observed
    :class:`Algorithm`; ``T`` is the type of `.value` in the reported
    :class:`AccountantRecord`. EvoKit does not use or require them.

    Tutorial: :doc:`../guides/examples/accountant`.

    """
    def __init__(self: Self,
                 handlers: dict[Container[str], Callable[[C], Any]]):
        """
        Args:
            handlers: a dictionary of `event : handler` mappings.
                Each `handler` should have the signature
                :python:`Algorithm -> Any`:
        """
        #: Records collected by the ``Accountant``
        self._records: list[AccountantRecord] = []

        #: `Event - handler` pairs of the ``Accountant``
        self.handlers: dict[Container[str], Callable[[C], Any]] = handlers

        #: The attached :class:`Algorithm`
        self._subject: Optional[C] = None

    def _subscribe(self: Self, subject: C) -> None:
        """Machinery.

        :meta private:

        Subscribe for events in a :class:`.Algorithm`.

        Args:
            subject: the :class:`.Algorithm` whose events are monitored by
                this accountant.
        """
        self._subject = subject

    def _update(self: Self, event: str) -> None:
        """Machinery.

        :meta private:

        When the attached :class:`.Algorithm` calls :meth:`.Algorithm.update`,
        it calls this method on every registered accountant.

        When an event matches a key in :attr:`handlers`, call the corresponding
        value with the attached Algorithm as argument. Store the result in
        :attr:`records`.

        Raise:
            RuntimeError: If no :class:`Algorithm` is attached.
        """
        if self._subject is None:
            raise RuntimeError("Accountant updated without a subject.")
        else:
            for trigger, action in self.handlers.items():
                if event in trigger:
                    self._records.append(
                        AccountantRecord(event,
                                         self._subject.generation,
                                         action(self._subject)))

    def report(self: Self,
               scope: Optional[str | int]) -> list[AccountantRecord]:
        """Report collected records.

        Args:
            scope: Option to filter which records to report.
            * If :arg:`scope` is an :class:`int` : report record
              only if :python:`record.generation==scope`.
            * If :arg:`scope` is an :class:`str` : report record
              only if :python:`record.event==scope`.
            * Otherwise, of if (by default) ``scope==None``,
              report all records.

        Each time an event fires in the attached :class:`.Algorithm`,
        if that event is registered in :attr:`handlers`, supply the
        :class:`.Algorithm` to the handler as argument then collect
        the result in an :class:`.AccountantRecord`. This method
        returns a list of all collected records.
        """
        if not self.is_registered():
            raise ValueError("Accountant is not attached to an algorithm;"
                             " cannot publish.")
        if isinstance(scope, int):
            return [r for r in self._records
                    if r.event == scope]
        if isinstance(scope, str):
            return [r for r in self._records
                    if r.generation == scope]
        else:
            return self._records

    def is_registered(self: Self) -> bool:
        """Return if this accountant is attached to an :class:`.Algorithm`.
        """
        return self._subject is not None

    @override
    def __len__(self: Self) -> int:
        return len(self._records)

    @overload
    def __getitem__(self: Self,
                    index: int) -> AccountantRecord[T]:
        pass

    @overload
    def __getitem__(self: Self,
                    index: slice) -> Sequence[AccountantRecord[T]]:
        pass

    @override
    def __getitem__(self: Self,
                    index: int | slice)\
            -> AccountantRecord[T] | Sequence[AccountantRecord[T]]:
        return self._records[index]
