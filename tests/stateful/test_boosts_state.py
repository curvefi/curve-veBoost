from collections import defaultdict
from typing import Tuple

from brownie import chain, convert
from brownie.network.account import Account

DAY = 86400
WEEK = DAY * 7


class Line:
    """Very simple line class with ability to add/subtract two together.

    Examples:

        >>> line = Line(-1, 4)
        >>> line.get_y(4)
        0
        >>> Line(-1, 4) + Line(1, 4)
        Line(slope=0.0000, bias=8.0000)
        >>> line += Line(1, 0)
        >>> line
        Line(slope=0.0000, bias=4.0000)
    """

    def __init__(self, slope: float, bias: float) -> None:
        self.slope = slope
        self.bias = bias

    def get_y(self, x: float) -> float:
        # y = mx + b
        return self.slope * x + self.bias

    def get_x(self, y: float) -> float:
        # y = mx + b -> (y - b)/m = x
        return (y - self.bias) / self.slope

    @classmethod
    def from_two_points(cls, p1: Tuple[float, float], p2: Tuple[float, float]) -> "Line":
        _slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
        _bias = p1[1] - _slope * p1[0]
        return cls(_slope, _bias)

    def __repr__(self) -> str:
        return f"Line(slope={self.slope:.4f}, bias={self.bias:.4f})"

    def __add__(self, other: "Line") -> "Line":
        return Line(self.slope + other.slope, self.bias + other.bias)

    def __sub__(self, other: "Line") -> "Line":
        return Line(self.slope - other.slope, self.bias - other.bias)

    def __iadd__(self, other: "Line") -> "Line":
        self.slope += other.slope
        self.bias += other.bias
        return self

    def __isub__(self, other: "Line") -> "Line":
        self.slope -= other.slope
        self.bias -= other.bias
        return self


class _State:
    def __init__(self) -> None:
        self.balances = defaultdict(lambda: Line(0, 0))
        self.delegated = defaultdict(lambda: Line(0, 0))
        self.received = defaultdict(lambda: Line(0, 0))
        self.tokens = defaultdict(lambda: Line(0, 0))

    @staticmethod
    def get_token_id(delegator: Account, _id: int) -> int:
        return (convert.to_uint(delegator.address) << 96) + _id

    def get_delegator(token_id: int):
        return convert.to_address(convert.to_bytes(token_id >> 96))

    def create_boost(
        self,
        delegator: Account,
        receiver: Account,
        percentage: int,
        cancel_time: int,
        expire_time: int,
        _id: int,
    ) -> None:
        now = chain.time()

        assert 0 < percentage <= 10_000
        assert cancel_time <= expire_time <= self.balances[delegator].get_x(0)
        assert expire_time - now >= WEEK
        assert _id < 2 ** 96

        balance = self.balances[delegator].get_y(now)
        delegated = self.delegated[delegator].get_y(now)
        assert delegated >= 0

        y = percentage * (balance - delegated) // 10_000
        assert y > 0

        line = Line.from_two_points((now, y), (expire_time, 0))
        assert line.slope < 0

        self.delegated[delegator] += line
        self.received[receiver] += line
        self.tokens[self.get_token_id(delegator, _id)] += line
