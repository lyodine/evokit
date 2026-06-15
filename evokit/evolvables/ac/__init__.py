from __future__ import annotations
from ..algorithms import HomogeneousAlgorithm
from typing import Self, TypeVar, Any
from ...core.population import Individual, Population
from typing import Optional
from ...core.variator import Variator
from typing import override
import random
from abc import ABC, abstractmethod

DM = TypeVar("DM", bound=Individual[Any])


class CollisionSoup(HomogeneousAlgorithm[DM]):
    """Base class for all artificial chemistry
    systems.

    Artificial chemistry algorithms do not use
    selectors, variators, and evaluators; rather,
    change occurs according to a set of
    :class:`CollisionRule`\\ s: items that can react
    according to a rule are consumed to create its
    products.

    Individuals used in these algorithms must
    have hashable genomes.
    """
    def __init__(self: Self,
                 population: Population[DM],
                 rules: list[CollisionRule]) -> None:
        """
        """
        self.population: Population[DM] = population
        self.rules: list[CollisionRule] = rules

    @override
    def step(self: Self) -> None:
        for rule in self.rules:
            self.population = rule.vary_population(self.population)


class CollisionRule(Variator[DM], ABC):
    """Base class for all collision rules. Works
    with both :class:`.MoleculeSet` and :class:`.Population`

    Alternative to :class:`.Variator`. Whereas the variator
    takes a tuple from the population, a collision rule
    does the following:

    .. code-block::
        :linenos:

        molecules = draw(population)
        molecules.append(draw(population))

    Tutorial: :doc:`../guides/examples/onemax`.
    """
    from typing import Sequence
    NO_REACTION_TUPLE: tuple[DM] = tuple()

    def _attempt_reaction_helper(
            self: Self,
            drawn_molecules: list[DM],
            population: Population[DM]
    ) -> Optional[tuple[DM, ...]]:
        """Attempt an reaction after drawing
        :attr:`.arity` molecules.

        If the size of :arg:`drawn_molecules` is no less
        than :attr:`self.arity`, attempt a reaction.
        Otherwise, collect one more molecule then
        attempt a reaction in a recursive call.

        If the reaction cannot occur, return molecules drawn
        in this function to the population.
        """
        if self.arity is None:
            raise ValueError("CollisionRule: Arity is none; cannot draw"
                             " molecules for reaction.")
        try:
            reactant_indices = random.sample(range(0,
                                                   len(population)),
                                             self.arity)
        except ValueError:
            raise ValueError("Insufficient molecules in population")
        reactants = tuple(population[i] for i in reactant_indices)
        reaction_result: Optional[tuple[DM, ...]] =\
            self.react(reactants)

        if reaction_result is None:
            # If cannot react:
            # Do nothing; no molecules have been taken from the
            #   population yet.
            return tuple()
        else:
            # If can react:
            # Call :meth:`.vary` to let the
            #   framework know what happened.
            reaction_result = self.vary(reaction_result)
            # Return molecules to population
            for i in sorted(reactant_indices, reverse=True):
                del population[i]

            population.extend(reaction_result)

    def vary(self: Self,
             parents: Sequence[DM]) -> tuple[DM, ...]:
        """Identity.

        In a :class:`.CollisionRule`, the reaction
        is handled by :meth:`.react`. Still, :meth:`.vary`
        is called to provide framework support (e.g.
        to register reactants as parents of the results).

        Do not override this; override :meth:`.react`
        instead.
        """
        return tuple(parents)

    @abstractmethod
    def react(self: Self,
              parents: Sequence[DM]) -> Optional[tuple[DM, ...]]:
        """Attempt a reaction using :arg:`parents`.
        The length of :arg:`parents` is guaranteed to be
        :attr:`.arity`.

        Implementation should only use :attr:`.Individual.genome`
        to check if an reaction can occur.
        """

    @override
    def vary_population(self: Self,
                        population: Population[DM],
                        *args: Any,
                        **kwargs: Any) -> Population[DM]:
        """Vary the population.

        The default implementation separates ``population`` into groups
        of size `.arity`, call `.vary` with each group as argument,
        then collect and returns the result.

        Args:
            population: Population to vary.

        .. note::
            The default implementation calls :meth:`.Individual.reset_fitness`
            on each offspring to clear its fitness. Any implementation that
            overrides this method should do the same.
        """
        reaction_result = self._attempt_reaction_helper(
            drawn_molecules=[],
            population=population
        )
        if reaction_result is not None:
            population.extend(reaction_result)

        return population
