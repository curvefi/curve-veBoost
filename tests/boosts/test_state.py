from collections import defaultdict
from typing import DefaultDict

from brownie import convert
from brownie.network.account import Account
from dataclassy import dataclass

DAY = 86400
WEEK = DAY * 7
YEAR = DAY * 365


@dataclass(slots=True, iter=True)
class Point:
    """Representation of a point on a 2-D plane.

    Examples:

        >>> Point(0, 0)
        Point(x=0, y=0)
        >>> Point(0, 0) + Point(0, 1)
        Point(x=0, y=1)
        >>> Point(0, 1) - Point(0, 1)
        Point(x=0, y=0)
        >>> Point(1, 2) * 3
        Point(x=3, y=6)
    """

    x: int
    y: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other: int) -> "Point":
        assert isinstance(other, int)
        return Point(self.x * other, self.y * other)


@dataclass(slots=True, iter=True)
class Line:
    """Reperesentation of a line on a 2-D plane.

    Examples:

        >>> Line(0, 0)
        Line(slope=0, bias=0)
        >>> Line(0, 1) + Line(1, 1)
        Line(slope=1, bias=2)
        >>> Line(1, 1) - Line(1, 0)
        Line(slope=0, bias=1)
        >>> Line(1, 1) * 3
        Line(slope=3, bias=3)
        >>> list(Line(0, 1))
        [0, 1]
        >>> Line.from_two_points((0, 0), (1, 1))
        Line(slope=1, bias=0)
    """

    slope: int = 0
    bias: int = 0

    @classmethod
    def from_two_points(cls, a: Point, b: Point) -> "Line":
        """Generate a line which fits through two points.

        Uses integer division for calculating slope, similar to the EVM
        implementation of veBoost.
        """
        (x1, y1), (x2, y2) = a, b
        slope = (y2 - y1) // (x2 - x1)
        bias = y1 - slope * x1
        return cls(slope, bias)

    def __add__(self, other: "Line") -> "Line":
        return Line(self.slope + other.slope, self.bias + other.bias)

    def __sub__(self, other: "Line") -> "Line":
        return Line(self.slope - other.slope, self.bias - other.bias)

    def __mul__(self, other: int) -> "Line":
        assert isinstance(other, int)
        return Line(self.slope * other, self.bias * other)

    def __call__(self, x: int) -> int:
        return self.slope * x + self.bias


class Token(Line):
    """Representation of a Token's data fields.

    Examples:

        >>> Token()
        Token(slope=0, bias=0, delegator=None, owner=None, cancel_time=0)
        >>> Token(1, 1)
        Token(slope=1, bias=1, delegator=None, owner=None, cancel_time=0)
        >>> Token(1, 1) + Token(10, 0)
        Token(slope=11, bias=1, delegator=None, owner=None, cancel_time=0)
        >>> Token(1, 1) - Token(1, 0)
        Token(slope=0, bias=1, delegator=None, owner=None, cancel_time=0)
        >>> Token(1, 1) * 0
        Token(slope=0, bias=0, delegator=None, owner=None, cancel_time=0)
        >>> list(Token(0, 1))
        [0, 1, None, None, 0]
        >>> Token.from_two_points((0, 0), (1, 1))
        Token(slope=1, bias=0, delegator=None, owner=None, cancel_time=0)
    """

    delegator: Account = None
    owner: Account = None
    cancel_time: int = 0

    @classmethod
    def from_two_points(cls, a: Point, b: Point) -> "Line":
        return cls(*super().from_two_points(a, b))

    @property
    def expire_time(self):
        if self.slope == 0:
            return 0
        else:
            return -self.bias // self.slope

    def __add__(self, other: "Token") -> "Token":
        return Token(*super().__add__(other))

    def __sub__(self, other: "Token") -> "Token":
        return Token(*super().__sub__(other))

    def __mul__(self, other: int) -> "Token":
        assert isinstance(other, int)
        return Token(*super().__mul__(other))

    def __call__(self, x: int) -> int:
        return super().__call__(x)


@dataclass(slots=True, iter=True)
class Boost:

    delegated: Line = Line(0, 0)
    received: Line = Line(0, 0)


class ContractState:
    def __init__(self) -> None:

        self.boost: DefaultDict[Account, Boost] = defaultdict(Boost)
        self.boost_tokens: DefaultDict[int, Token] = defaultdict(Token)

    def create_boost(
        self,
        delegator: Account,
        receiver: Account,
        percentage: int,
        cancel_time: int,
        expire_time: int,
        _id: int,
        timestamp: int,
        vecrv_balance: int,
        lock_expiry: int,
        update_state: bool = False,
    ):
        assert 0 < percentage < 10_000  # percentage within bounds
        # cancel time before expire time, expire time before lock expiry
        assert cancel_time <= expire_time <= lock_expiry
        assert expire_time >= timestamp + WEEK  # expire time greater than min delegation time
        assert _id < 2 ** 96  # id with bounds

        delegated_boost: int = self.boost[delegator].delegated(timestamp)
        assert delegated_boost > 0  # no outstanding negative boosts

        y = percentage * (vecrv_balance - delegated_boost) // 10_000
        assert y > 0

        token: Token = Token.from_two_points((timestamp, y), (expire_time, 0))
        assert token.slope < 0

        token.delegator = delegator
        token.owner = receiver
        token.cancel_time = cancel_time

        token_id: int = self.get_token_id(delegator.address, _id)
        assert self.boost_tokens[token_id].owner is None

        # modify state last
        if update_state:
            self.boost_tokens[token_id] = token
            self.boost[delegator].delegated += token
            self.boost[receiver].received += token

    def extend_boost(
        self,
        token_id: int,
        percentage: int,
        expire_time: int,
        cancel_time: int,
        timestamp: int,
        vecrv_balance: int,
        lock_expiry: int,
        update_state: bool = False,
    ):
        assert 0 < percentage <= 10_000
        assert cancel_time <= expire_time <= lock_expiry
        assert expire_time >= timestamp + WEEK

        token: Token = self.boost_tokens[token_id]
        assert token.owner is not None

        token_current_value: int = token(timestamp)
        token_expiry: int = token.expire_time

        assert expire_time >= token_expiry
        if cancel_time < token.cancel_time:
            assert timestamp >= token_expiry

        delegated_boost: int = (self.boost[token.delegator].delegated - token)(timestamp)
        assert delegated_boost > 0

        y: int = percentage * (vecrv_balance - delegated_boost) // 10_000
        assert y > 0
        assert y >= token_current_value

        new_token: Token = Token.from_two_points((timestamp, y), (expire_time, 0))
        assert new_token.slope < 0

        new_token.delegator = token.delegator
        new_token.owner = token.owner
        new_token.cancel_time = cancel_time

        # modify state last
        if update_state:
            self.boost_tokens[token_id] = new_token
            self.boost[token.delegator].delegated -= token
            self.boost[token.delegator].delegated += new_token
            self.boost[token.owner].received -= token
            self.boost[token.owner].received += new_token

    def cancel_boost(
        self, token_id: int, caller: Account, timestamp: int, update_state: bool = False
    ):
        token: Token = self.boost_tokens[token_id]
        assert token.owner is not None
        if caller == token.owner:
            if caller == token.delegator:
                assert timestamp >= token.cancel_time
            else:
                assert timestamp >= token.expire_time

        if update_state:
            self.boost_tokens[token_id] *= 0
            self.boost[token.delegator].delegated -= token
            self.boost[token.owner].received -= token

    def transfer_from(self, _from: Account, _to: Account, token_id: int):
        pass

    @staticmethod
    def get_token_id(account: str, _id: int) -> int:
        return (convert.to_uint(account) << 96) + _id
