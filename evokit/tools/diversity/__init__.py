"""Toolset for diversity maintenance.


"""

from ...core import Population, Individual
from typing import Callable

from ..._utils.dependency import ensure_installed
ensure_installed("numpy")
import numpy as np


def share_fitness(pop: Population,
                  sigma_share: float,
                  alpha: float,
                  distance_measure: Callable[[Individual,
                                              Individual], float]) -> None:
    """Perform fitness sharing [#]_ by adjusting (in-place)
    the :attr:`.Individual.fitness` of each individual
    in a population.

    The fitness is updated according to the following
    expression:

    .. math::

        x_i\\mathrm{.fitness} \\leftarrow
        \\frac{x_i\\mathrm{.fitness}}{\\sum^{|\\mathcal{P}|}_{j}
        {\\mathrm{sh}\\,(d(x_i,x_j))}}

    where

    .. math::
        :nowrap:

        \\[
        \\mathrm{sh}\\,(k) =
        \\left\\{
        \\begin{array}{ll}
            1 - (k / \\sigma_{\\mathrm{share}})^{\\alpha}
                & \\mathrm{if}~k \\le \\sigma_{\\mathrm{share}} \\\\
            0 & \\mathrm{otherwise.}
        \\end{array}
        \\right.
        \\]

    .. [#] *Genetic Algorithms with Sharing for
        Multi-Modal Function Optimization*
    """
    """
    """
    def sh(k: float, sigma_share: float, alpha: float):
        return 1 - (k / sigma_share)**alpha \
            if k <= sigma_share else 0

    ind: Individual
    for ind in pop:
        ind.fitness = ind.fitness /\
            np.sum([sh(distance_measure(ind_other, ind),
                       sigma_share,
                       alpha) for ind_other in pop])
