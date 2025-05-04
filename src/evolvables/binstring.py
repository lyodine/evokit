import random
import typing
from typing import Optional, Tuple, TypeVar

from core.controller import LinearController
from core.evaluator import Evaluator
from core.population import Individual
from core.population import Population
from core.selector import Elitist
from core.selector import SimpleSelector

from core.variator import Variator


class IllegalVariation(Exception):
    def __init__(self):
        super().__init__("Given index out of bound!")


T = TypeVar('T', bound=Individual)


class Binary(Individual[T]):
    def __init__(self, len: int, value: typing.Optional[int] = None) -> None:
        super().__init__()
        self.length = len
        if (value is None):
            self._value = 0
        else:
            self._value = value

    def _assert_index_is_valid(self, pos: int):
        if pos >= self.length:
            raise IllegalVariation

    # def set(self, pos: int):
    #     self._assert_index_is_valid(pos)
    #     self._value = self._value | (1 << pos)

    # def clear(self, pos: int):
    #     self._assert_index_is_valid(pos)
    #     self._value =  self._value & ~(1 << pos)

    # def get (self, pos: int)-> int :
    #     self._assert_index_is_valid(pos)
    #     return (self._value >> pos) & 1

    def toggle(self, pos: int):
        self._assert_index_is_valid(pos)
        self._value = (self._value ^ (1 << (pos)))

    def __len__(self) -> int:
        return self.length

    @classmethod
    def create_random(cls, len: int) -> typing.Self:
        bin = cls(len)
        for i in range(0, len):
            if (bool(random.getrandbits(1))):
                bin.toggle(i)
        return bin

    @property
    def value(self):
        return self._value

    def copy(self) -> typing.Self:
        new_copy = self.__class__(self.length, self.value)
        return new_copy

    __deepcopy__ = copy
    __copy__ = copy

    def __str__(self):
        # return str(bin(self._value))[2:].ljust(self.length, '0')
        return str(bin(self._value))[2:].rjust(self.length, '0')


class BitDistanceEvaluator(Evaluator[Binary]):
    def evaluate(self, s1: Binary) -> float:
        return s1._value.bit_count()


class RandomBitMutator(Variator[Binary]):
    def __init__(self):
        super().__init__(1, 2)

    def vary(self, parents: Tuple[Binary, ...], **kwargs) -> Tuple[Binary, ...]:
        binary = parents[0].copy()
        newbits = parents[0].copy()

        for i in range(0, len(binary)):  # Somehow cannot properly implement __len__
            if (random.random()<0.001):
                binary.toggle(i)
                newbits.toggle(i)
        return (binary, newbits)


if __name__ == "__main__":
    init_pop = Population[Binary]()

    for i in range(0, 1):
        init_pop.append(Binary.create_random(10))

    evaluator = BitDistanceEvaluator()
    pselector = Elitist(SimpleSelector[Binary](10))
    cselector = Elitist(SimpleSelector[Binary](10))
    variator = RandomBitMutator()

    ctrl: LinearController = LinearController(
        population=init_pop,
        parent_evaluator=evaluator,
        parent_selector=pselector,
        variator=variator,
        survivor_evaluator=evaluator,
        survivor_selector=cselector,
    )

    dicts: typing.Dict[int, Optional[float]] = {}

    from core.accountant import Accountant

    # Ignore type checking. Because `Accountant` is defined for the
    #       `Controller` class, which does not necessarily have one
    #       `population`, type checkers report error on this line.\
    # Because an LinearController is registered with this `Accountant`,
    #       we can be _somewhat_ sure that the accountant's suject has
    #       a `.population`.
    #
    acc = Accountant({"GENERATION_BEGIN": lambda x: len(x.population)})  # type:ignore

    ctrl.register(acc)

    for i in range(0, 100):
        ctrl.step()
        dicts[i] = ctrl.population[0].fitness

    print(dicts)

    print(acc.publish())