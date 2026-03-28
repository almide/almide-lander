import Foundation

@main
struct TestApp {
    static func main() {
        let d = distance(a: Point(x: 0.0, y: 0.0), b: Point(x: 3.0, y: 4.0))
        print("distance = \(d)")
        assert(abs(d - 5.0) < 0.001)

        let a = area(shape: Shape.circle(radius: 5.0))
        print("area(circle(5)) = \(a)")
        assert(abs(a - 78.54) < 0.1)

        let mid = midpoint(a: Point(x: 0.0, y: 0.0), b: Point(x: 10.0, y: 10.0))
        print("midpoint = (\(mid.x), \(mid.y))")
        assert(abs(mid.x - 5.0) < 0.001)

        let desc = describe(shape: Shape.rect(width: 3.0, height: 4.0))
        print("describe = \(desc)")
        assert(desc.contains("rectangle"))

        print("")
        print("UniFFI Swift: ALL TESTS PASSED")
    }
}
