import math


def sin(x: float) -> float:
    return math.sin(x)


def cos(x: float) -> float:
    return math.cos(x)


def tan(x: float) -> float:
    return math.tan(x)


def add(x: float, y: float) -> float:
    return x + y


def sub(x: float, y: float) -> float:
    return x - y


def mul(x: float, y: float) -> float:
    return x * y


def div(x: float, y: float) -> float:
    if y == 0:
        return 1
    return x / y


def avg(x: float, y: float) -> float:
    return (x + y) / 2


def lim(x: float, max_val: float, min_val: float) -> float:
    return max(min(max_val, x), min_val)
