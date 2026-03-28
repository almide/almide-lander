"""End-to-end test: Almide mathlib via UniFFI Python bindings"""
from almide_mathlib import Point, Shape, distance, area, midpoint, describe

d = distance(Point(x=0.0, y=0.0), Point(x=3.0, y=4.0))
print(f"distance = {d}")
assert abs(d - 5.0) < 0.001

a = area(Shape.CIRCLE(radius=5.0))
print(f"area(circle(5)) = {a}")
assert abs(a - 78.54) < 0.1

mid = midpoint(Point(x=0.0, y=0.0), Point(x=10.0, y=10.0))
print(f"midpoint = ({mid.x}, {mid.y})")
assert abs(mid.x - 5.0) < 0.001

desc = describe(Shape.RECT(width=3.0, height=4.0))
print(f"describe = {desc}")
assert "rectangle" in desc

print("\nALL TESTS PASSED")
