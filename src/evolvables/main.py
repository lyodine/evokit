import typing
import random
from typing import TypeVar
from typing import Tuple
from typing import Optional
from core.controller import Controller
from core.evaluator import Evaluator
from core.population import Population
from core.population import Genome
from core.variator import Variator
from core.controller import Controller
from core.selector import Elitist
from core.selector import SimpleSelector
from core.selector import TournamentSelector


class IllegalVariation(Exception):
    def __init__(self):
        super().__init__("Given index out of bound!")

T = TypeVar('T', bound=Genome)

class Binary(Genome[T]):
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
    def create_random(cls, len:int) -> typing.Self:
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
    def __init__ (self):
        super().__init__(1, 2)

    def vary(self, parents: Tuple[Binary, ...], **kwargs) -> Tuple[Binary, ...]:
        binary = parents[0].copy()
        newbits = parents[0].copy()
        
        for i in range(0, len(binary)): # Somehow cannot properly implement the __len__ dunder 
            if (random.random()<0.001):
                binary.toggle(i)
                newbits.toggle(i)
        return (binary, newbits)

init_pop = Population[Binary]()

for i in range (0, 10):
    init_pop.append(Binary.create_random(10))

evaluator = BitDistanceEvaluator()
pselector = Elitist(SimpleSelector[Binary](1, 10))
cselector = Elitist(SimpleSelector[Binary](1, 10))
variator = RandomBitMutator()

ctrl = Controller[Binary] (
    population = init_pop,
    evaluator = evaluator,
    variator = variator,
    offspring_selector = pselector,
    parent_selector = cselector
)

dicts : typing.Dict[int, Optional[float]]= {}

for i in range(0, 100):
    ctrl.step()
    dicts[i] = ctrl.population[0].score

print (dicts)