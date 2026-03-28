# End-to-end test: Almide mathlib via Magnus
require_relative 'almide_mathlib'

p1 = AlmideMathlib::Point.new(0.0, 0.0)
p2 = AlmideMathlib::Point.new(3.0, 4.0)

d = AlmideMathlib.distance(p1, p2)
puts "distance = #{d}"
raise "expected 5.0" unless (d - 5.0).abs < 0.001

mid = AlmideMathlib.midpoint(p1, p2)
puts "midpoint = (#{mid.x}, #{mid.y})"
raise "expected 1.5" unless (mid.x - 1.5).abs < 0.001

c = AlmideMathlib::Shape.circle(5.0)
a = AlmideMathlib.area(c)
puts "area(circle(5)) = #{a}"
raise "expected ~78.54" unless (a - 78.54).abs < 0.1

r = AlmideMathlib::Shape.rect(3.0, 4.0)
puts "area(rect(3,4)) = #{AlmideMathlib.area(r)}"
puts "describe = #{AlmideMathlib.describe(c)}"

puts "\nALL TESTS PASSED"
