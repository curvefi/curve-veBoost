from typing import Tuple


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
