from concurrent.futures import ProcessPoolExecutor
from typing import TypeVar
from typing import Callable
from typing import Sequence
from typing import Optional
from typing import Any
from concurrent.futures.process import BrokenProcessPool

from ..._utils.addons import is_installed

import copy

if is_installed("multiprocess"):
    from multiprocess.pool import Pool  # type: ignore
    import dill  # type: ignore
    dill.settings['recurse'] = True  # type: ignore
else:
    from multiprocessing.pool import Pool

S = TypeVar("S")
A = TypeVar("A")
type AS[A] = Sequence[A]
B = TypeVar("B")


def parallelise_task[S, A, B](
        # PEP 646 signature
        fn: Callable[[S, A], B],
        self: S,
        iterable: Sequence[A],
        processes: Optional[int | ProcessPoolExecutor | Pool],
        share_self: bool) -> Sequence[B]:
    """Parallelise tasks such as variation and evaluation.

    Default implementations in :meth:`Variator.vary_population`
    and :meth:`Evaluator.evaluate_population` use this method.

    .. warning::
        Consider installing `multiprocess` (by the author
        of `dill`) if you run into any trouble with multiprocessing.

        Do not give :class:`multiprocessing.pool.Pool`
        in :arg:`processes`. Instead, consider using either
        an integer, or a :class:`multiprocess.pool.Pool`, or
        a :class:`concurrent.futures.ProcessPoolExecutor`.

        The :mod:`multiprocessing` module, which is part of the
        standard library, uses pickle. This means a `self`,
        which contains lambdas, complex objects, and most
        complex objects created in a Jupyter notebook,
        would crash worker processes. This is impossible
        to detect and correct in :class:`multiprocessing.pool.Pool`
        because it would attempt to restart crashed
        workers, which leads to indefinite hanging.

        Correcting this would require a significant
        investment in time and diving quite deep into the
        Python source code. This is beyond the Developer's
        capabilities.

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

            * If (by default) ``processes==None``:
              Do not parallelise.

            To use all available processors, set :arg:`processes`
            to :meth:`os.process_cpu_count`.

        share_self: If :python:`True`, share a deep copy
            of ``self`` to each worker process.
            Non-serialisable attributes are replaced with
            :python:`None` instead.

            If :arg:`processes` is :python:`None`, then this argument has
            no effect.
    """

    if processes is None:
        return [fn(self, each) for each in iterable]
    elif isinstance(processes, ProcessPoolExecutor):
        return _execute_with_executor(
            processes, fn, self, iterable, share_self)
    else:
        if isinstance(processes, int):
            if is_installed("multiprocess"):
                return _execute_with_pool(
                    processes, fn, self, iterable, share_self)
            else:
                return _execute_with_executor(
                    processes, fn, self, iterable, share_self)
        else:
            if not is_installed("multiprocess"):
                raise NotImplementedError(
                    "A `multiprocessing.pool.Pool`"
                    " is given in `processes`. This may "
                    " lead to unforeseen consequences.\n"
                    "Specifically, the program may hang"
                    " indefinitely with no way to detect"
                    " if work is being done. It would be"
                    " impossible to detect if this has"
                    " occurred.\n"
                    "The consequence can be catastrophic\n"
                    " on HPCs, where resources are costly."
                    " Please either install and use"
                    " `multiprocess.Pool` or use a"
                    " concurrent.futures.ProcessPoolExecutor.\n"
                    "Sorry for the inconvenience.")
            else:
                return _execute_with_pool(processes, fn, self,
                                          iterable,
                                          share_self)


def _duplicate_self[S, A](self: S,
                          share_self: bool,
                          iterable: Sequence[A],)\
        -> Sequence[S] | Sequence[None]:
    if share_self:
        return [copy.deepcopy(self)
                for _ in range(len(iterable))]
    else:
        return [None for _ in range(len(iterable))]


def _execute_with_executor[S, A, B](processes: ProcessPoolExecutor | int,
                                    fn: Callable[[S, A], B],
                                    self: S,
                                    iterable: Sequence[A],
                                    share_self: bool) -> Sequence[B]:
    try:
        if isinstance(processes, int):
            with ProcessPoolExecutor(max_workers=processes) as exec:
                return list(exec.map(fn,
                                     _duplicate_self(self,
                                                     share_self,
                                                     iterable),
                                     iterable))
        else:
            return list(processes.map(fn,
                                      _duplicate_self(self,
                                                      share_self,
                                                      iterable),
                                      iterable))
    except BrokenProcessPool:
        raise NotImplementedError(
            """Work in a worker process has abruptly halted.

This might be because the OS killed it
(due to, for example, memory issues), or
the worker may have exited.

It is possible that some shared data cannot
be pickled. This might happen if an argument
instantiates a class that is declared in a
Jupyter notebook, or if the argument is a
function defined in a Jupyter notebook.

Please consider installing the package
`multiprocess`. This package uses `dill`, a
slower but more powerful serialiser by
the same author. Alternatively, change
either the operator of individual
representations to evade the problem.
""")


def _execute_with_pool[S, A, B](processes: Pool | int,
                                fn: Callable[[S, A], B],
                                self: S,
                                iterable: Sequence[A],
                                share_self: bool) -> Sequence[B]:
    # First, execute a task to see what happens

    results: Sequence[B]

    if isinstance(processes, int):
        with Pool(processes) as pool:
            futures = [pool.apply_async(func=fn,
                                        args=[self, it])
                       for it in iterable]

            results = [*[fut.get() for fut in futures]]

    else:
        results = processes.starmap(
            fn, [[self, it] for it in iterable]
        )
        # futures = [processes.apply_async(func=fn,
        #                                  args=[sf, it]) for sf, it
        #            in zip(our_selves, iterable)]
        # results = [*[fut.get() for fut in futures]]

    return results


def __getstate__(self: object) -> dict[str, Any]:
    """Machinery.

    :meta private:

    Ensure that when this object is pickled, its process pool,
    if any is defined (see :meth:`Variator.processes` and
    `Evaluator.processes`), is not pickled.
    """
    self_dict = self.__dict__.copy()
    del self_dict['processes']
    return self_dict


def __deepcopy__(self: object, memo: dict[int, Any]):
    """Machinery.

    :meta private:

    Ensure that when this object is shared by processes,
    its non-serialisable members are not copied.
    """
    new_self = type(self).__new__(type(self))
    # Making sure nothing is copied for more than once.
    memo[id(self)] = new_self
    for key, value in self.__dict__.items():
        can_pickle_this: bool
        try:
            can_pickle_this =\
                dill.pickles(value)   # type: ignore[TypeError]
        except Exception:
            # If an exception arises when determining if the
            #   object can be pickled .. probably not.
            can_pickle_this = False
        setattr(new_self, key, copy.deepcopy(
            value if can_pickle_this else None, memo))

    return new_self
# def _execute_tasks[S, A, B](pool: Pool,
#                             fn: Callable[[S, A], B],
#                             self: S,
#                             iterable: Sequence[A],
#                             share_self: bool) -> Sequence[B]:
#     # First, execute a task to see what happens

#     our_selves: list[S | object] = []

#     if share_self:
#         our_selves = [copy.deepcopy(self)
#                       for _ in range(len(iterable))]
#     else:
#         our_selves = [None for _ in range(len(iterable))]

#     # = processes
#     futures = [pool.apply_async(func=fn,
#                args=[sf, it]) for sf, it
#                in zip(our_selves[1:], iterable[1:])]

#     return [*[fut.get() for fut in futures]]
