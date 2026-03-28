"""End-to-end test: Almide mathlib via PyO3"""
from almide_mathlib import Point, Shape, distance, area, midpoint, describe

p1 = Point(x=0.0, y=0.0)
p2 = Point(x=3.0, y=4.0)

d = distance(p1, p2)
print(f"distance((0,0), (3,4)) = {d}")
assert abs(d - 5.0) < 0.001

mid = midpoint(p1, p2)
print(f"midpoint = ({mid.x}, {mid.y})")
assert abs(mid.x - 1.5) < 0.001
assert abs(mid.y - 2.0) < 0.001

c = Shape.circle(5.0)
r = Shape.rect(3.0, 4.0)
print(f"area(circle(5)) = {area(c)}")
print(f"area(rect(3,4)) = {area(r)}")
assert abs(area(c) - 78.54) < 0.1
assert abs(area(r) - 12.0) < 0.001

print(f"describe(circle) = '{describe(c)}'")
print(f"describe(rect) = '{describe(r)}'")

print("\nALL TESTS PASSED")
