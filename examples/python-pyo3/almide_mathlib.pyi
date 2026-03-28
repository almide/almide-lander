"""Almide module: mathlib"""

class Point:
    """A 2D point with x and y coordinates."""
    x: float
    y: float
    def __init__(self, x: float, y: float) -> None: ...

class Shape:
    """A geometric shape."""
    @staticmethod
    def circle(v0: float) -> Shape: ...
    @staticmethod
    def rect(v0: float, v1: float) -> Shape: ...

def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    ...

def area(shape: Shape) -> float:
    """Area of a geometric shape."""
    ...

def midpoint(a: Point, b: Point) -> Point:
    """Midpoint between two points."""
    ...

def describe(shape: Shape) -> str:
    """Human-readable description of a shape."""
    ...
