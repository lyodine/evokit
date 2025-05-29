from concurrent.futures import ProcessPoolExecutor
from typing import TypeVar
from typing import Callable
from typing import Sequence
from typing import Optional
from typing import Iterator

import copy

S = TypeVar("S")
A = TypeVar("A")
B = TypeVar("B")


def parallelise_task[S, A, B](
        fn: Callable[[S, A], B],
        self: S,
        iterable: Sequence[A],
        processes: Optional[int | ProcessPoolExecutor] = None,
        share_self: bool = False) -> Sequence[B]:
    """Parallelise tasks such as variation and evaluation.

    Default implementations in :meth:`Variator.vary_population`
    and :meth:`Evaluator.evaluate_population` use this method.

    Args:
        fn: Task to be parallelised.

        self: The caller, which might be shared by worker
            processes if :arg:`share_self` is :python:`True`.

        iterable: Data to be processed in parallel.

        processes: Option that decides how may processes to use.
            Can be an :class:`int`, a :class:`ProcessPoolExecutor`,
            or :python:`None`.

            * If :arg:`processes` is an :class:`int`: create a new
                :class:`ProcessPoolExecutor` with :arg:`processes` workers,
                then use it to execute the task. On Windows, it must be at
                most 61.

            * If :arg:`processes` is a :class:`ProcessPoolExecutor`:
                use it to execute the task.

            * If (by default) ``processes==None``: Do not parallelise.

            To use all available processors, set :arg:`processes`
            to :meth:`os.process_cpu_count`.

        share_self: If :python:`True`, share a deep copy
            of ``self`` to each worker process.
            Non-serialisable attributes are replaced with
            :python:`None` instead.

            If :arg:`processes` is :python:`None`, then this argument has
            no effect.

            Unfortunately, it is `not possible` to share an
            arbitrary :arg:`self` without knowing its attributes.
            The fact that all of this must be done in the
            variator itself, which is to be shared, compounds the
            problem.
    """

    if processes is None:
        return [fn(self, each) for each in iterable]

    executor: ProcessPoolExecutor

    if isinstance(processes, int):
        executor = ProcessPoolExecutor(max_workers=processes)
    else:
        assert isinstance(processes, ProcessPoolExecutor)
        executor = processes

    our_selves: list[S | object] = []

    if share_self:
        our_selves = [copy.deepcopy(self)
                      for _ in range(len(iterable))]
    else:
        our_selves = [None for _ in range(len(iterable))]

    nested_results: Iterator[B] =\
        executor.map(fn,
                     our_selves,
                     iterable,
                     timeout=None,
                     chunksize=1)

    return [*nested_results]
