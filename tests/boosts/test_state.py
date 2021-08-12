from brownie.network.account import Account
from dataclassy import dataclass


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

    def __add__(self, other: "Token") -> "Token":
        return Token(*super().__add__(other))

    def __sub__(self, other: "Token") -> "Token":
        return Token(*super().__sub__(other))

    def __mul__(self, other: int) -> "Token":
        assert isinstance(other, int)
        return Token(*super().__mul__(other))

    def __call__(self, x: int) -> int:
        return super().__call__(x)
