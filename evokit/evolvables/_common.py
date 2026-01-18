"""This module contains functions that act on built-in
types. These functions should only be used by modules and
packages in :mod:`.evolvables` and are always subject to
change.
"""
from typing import Iterable
import random


def crossover[R](seq_1: list[R],
                 seq_2: list[R],
                 k: int,
                 allow_repeat: bool = True,
                 even: bool = True) -> tuple[list[R],
                                             list[R],]:
    """Perform k-point crossover with :arg:`seq_1` and
    :arg:`seq_2` as parents.

    Args:
        seq_1: A parent.

        seq_2: A parent.

        k: The number of crossover points.

        allow_repeat: If ``True``, then crossover segments
            can be empty. Swapping any segment with an empty
            segment effectively moves it to the empty segment's
            index.

        even: If ``True``, then crossover segments must have the
            same size and each offspring has the same size as its
            "direct" parent (parent where the offspring takes its
            first segment from). Otherwise, offspring can have
            different lengths.
    """
    seq_1 = seq_1.copy()
    seq_2 = seq_2.copy()

    seq_1_crossover_points: list[int]
    seq_2_crossover_points: list[int]

    if even:
        min_len = min(len(seq_1), len(seq_2))
        seq_1_crossover_points = generate_indices(min_len,
                                                  k,
                                                  allow_repeat)

        seq_2_crossover_points = seq_1_crossover_points
    else:
        seq_1_crossover_points = generate_indices(len(seq_1),
                                                  k,
                                                  allow_repeat)

        seq_2_crossover_points = generate_indices(len(seq_2),
                                                  k,
                                                  allow_repeat)

    return crossover_at_points(
        seq_1,
        seq_2,
        seq_1_crossover_points,
        seq_2_crossover_points,
    )


def generate_indices(seq_len: int,
                     k: int,
                     allow_repeat: bool) -> list[int]:
    """Uniformly generate random indices for a sequence
    of length :arg:`seq_len`.

    Args:
        seq_len: Length of the sequence to generate indices for.

        k: Number of indices to generate.

        allow_repeat: If ``True``, then returned indices can
            have repeats. Otherwise, otherwise.
    """
    if allow_repeat:
        return sorted([random.randint(0, seq_len - 1)
                       for _ in range(k)])
    else:
        assert k <= seq_len, f"More crossover points ({k})"
        f" than loci ({seq_len})"

        return list(random.sample(range(seq_len), k))


def crossover_at_points[R](seq_1: list[R],
                           seq_2: list[R],
                           seq_1_crossover_points: list[int],
                           seq_2_crossover_points: list[int],)\
        -> tuple[list[R], list[R],]:
    seq_1 = seq_1.copy()
    seq_2 = seq_2.copy()

    seq_1_crossover_point_pairs =\
        list(zip([None] + seq_1_crossover_points,
                 seq_1_crossover_points + [None]))[1::2]

    seq_2_crossover_point_pairs =\
        list(zip([None] + seq_2_crossover_points,
                 seq_2_crossover_points + [None]))[1::2]

    for (a_1, b_1), (a_2, b_2) in zip(seq_1_crossover_point_pairs,
                                      seq_2_crossover_point_pairs):
        seq_1[a_1:b_1], seq_2[a_2:b_2] = seq_2[a_2:b_2], seq_1[a_1:b_1]

    return (seq_1, seq_2)


def crossover_secundum[R](seq_1: list[R],
                          seq_2: list[R],
                          k: int,) -> tuple[list[R],
                                            list[R],]:
    """Alternative implementation of :meth:`crossover_at_points`.

    At the time of commit, ``%%timeit`` shows this
    method to be 20% slower than :meth:`uneven_crossover`.

    Still, this method is preserved for future testing. With
    luck (heh), maybe it will perform better in some settings.
    """
    seq_1_points: list[int] = sorted([random.randint(0, len(seq_1) - 1)
                                      for _ in range(k)])

    seq_2_points: list[int] = sorted([random.randint(0, len(seq_2) - 1)
                                      for _ in range(k)])

    seq_1_blocks = [seq_1[i:j] for i, j in zip([None] + seq_1_points,
                                               seq_1_points + [None])]

    seq_2_blocks = [seq_2[i:j] for i, j in zip([None] + seq_2_points,
                                               seq_2_points + [None])]

    return (
        unpack_nested(unpack_nested(zip(seq_1_blocks[::2],
                                        seq_2_blocks[1::2]))),
        unpack_nested(unpack_nested(zip(seq_2_blocks[::2],
                                        seq_1_blocks[1::2])))
    )


def unpack_nested[T](nested: Iterable[Iterable[T]]) -> list[T]:
    """Unpack a nested iterable. Returns the result
    as a list.

    Args:
        nested_list: The list the unpack.
    """
    # ``%%timeit`` shows this approach to be 2 times faster than
    #   ``sum``. Can change to ``sum`` or another implementation,
    #   if that implementation is faster.
    return [x for y in nested for x in y]
