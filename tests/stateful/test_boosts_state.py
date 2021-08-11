from collections import defaultdict
from typing import Tuple

from brownie import accounts, chain, convert
from brownie.network.account import Account
from brownie.test import strategy

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


class Token(Line):
    def __init__(self, cancel_time: int, receiver: Account = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cancel_time = cancel_time
        self.receiver = receiver

    @classmethod
    def from_two_points(cls, cancel_time: int, receiver: int, *args, **kwargs) -> "Line":
        return cls(cancel_time, receiver, *args, **kwargs)


class _State:
    def __init__(self) -> None:
        self.delegated = defaultdict(lambda: Line(0, 0))
        self.received = defaultdict(lambda: Line(0, 0))
        self.tokens = defaultdict(lambda: Token(0, None, 0, 0))

    @staticmethod
    def get_token_id(delegator: Account, _id: int) -> int:
        return (convert.to_uint(delegator.address) << 96) + _id

    @staticmethod
    def get_delegator(token_id: int) -> Account:
        return accounts.at(convert.to_address(convert.to_bytes(token_id >> 96)))

    def create_boost(
        self,
        vecrv_balance: int,
        lock_end: int,
        delegator: Account,
        receiver: Account,
        percentage: int,
        cancel_time: int,
        expire_time: int,
        _id: int,
    ) -> None:
        now = chain.time()

        assert 0 < percentage <= 10_000
        assert cancel_time <= expire_time <= lock_end
        assert expire_time - now >= WEEK
        assert _id < 2 ** 96

        balance = vecrv_balance
        delegated = self.delegated[delegator].get_y(now)
        assert delegated >= 0

        y = percentage * (balance - delegated) // 10_000
        assert y > 0

        line = Line.from_two_points((now, y), (expire_time, 0))
        assert line.slope < 0

        self.delegated[delegator] += line
        self.received[receiver] += line
        self.tokens[self.get_token_id(delegator, _id)] = Token(0, receiver, line.slope, line.bias)

    def extend_boost(
        self,
        vecrv_balance: int,
        lock_end: int,
        token_id: int,
        percentage: int,
        expire_time: int,
        cancel_time: int,
    ):
        delegator = self.get_delegator(token_id)
        now = chain.time()

        assert 0 < percentage <= 10_000
        assert cancel_time <= expire_time <= lock_end
        assert expire_time - now >= WEEK
        assert token_id < 2 ** 96

        token = self.tokens[token_id]

        assert expire_time >= token.get_x(0)
        if cancel_time < token.cancel_time:
            assert now >= token.get_x(0)

        dline = self.delegated[delegator] - token
        rline = self.received[token.receiver] - token

        balance = vecrv_balance
        delegated = dline.get_y(now)
        assert delegated >= 0

        y = percentage * (balance - delegated) // 10_000
        assert y > 0

        assert y >= token.get_y(now)

        new_token = Token.from_two_points(token.receiver, cancel_time, (now, y), (expire_time, 0))

        assert new_token.slope < 0

        self.delegated[delegator] = dline + new_token
        self.received[token.receiver] = rline + new_token
        self.tokens[token_id] = new_token

    def cancel_boost(self, token_id: int):
        delegator = self.get_delegator(token_id)
        token = self.tokens[token_id]

        self.delegated[delegator] -= token
        self.received[token.receiver] -= token
        self.tokens[token_id] = Token(0, None, 0, 0)

    def transfer_boost(self, _from: Account, _to: Account, token_id: int):
        token = self.tokens[token_id]

        assert _from == token.receiver

        self.received[_from] -= token
        self.received[_to] += token


class StateMachine:

    lock_amount = strategy("uint80", min_value=10 ** 18)
    lock_timedelta = strategy("uint32", max_value=DAY * 365 * 4 - 1, min_value=WEEK)
    account = strategy("address")

    def __init__(cls, accounts, crv, vecrv, veboost) -> None:
        cls.accounts = accounts
        cls.crv = crv
        cls.vecrv = vecrv
        cls.veboost = veboost

    def setup(self):

        total_supply = self.crv.balanceOf(accounts[0])
        amount = total_supply // 10

        self.state = _State()

        for account in self.accounts:
            self.crv.transfer(account, amount, {"from": accounts[0]})
            self.crv.approve(self.vecrv, 2 ** 256 - 1, {"from": account})

    def initialize_lock_half(self):
        for account in self.accounts[:5]:
            length = ((chain.time() + DAY * 365 * 4) // WEEK) * WEEK
            self.vecrv.create_lock(self.crv.balanceOf(account), length, {"from": account})

    def rule_lock_crv(self, account, lock_amount, lock_timedelta):
        if self.crv.balanceOf(account) < lock_amount:
            return

        lock_end = self.vecrv.locked__end(account)
        now = chain.time()
        if lock_end <= now:
            # no existing lock or previous lock expired
            if lock_end:
                self.vecrv.withdraw({"from": account})
            self.vecrv.create_lock(lock_amount, now + lock_timedelta, {"from": account})


def test_state(state_machine, accounts, crv, vecrv, veboost):
    state_machine(StateMachine, accounts, crv, vecrv, veboost)
