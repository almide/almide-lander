use magnus::{prelude::*, function, method, define_module, define_class, Ruby, Error, Value};
use std::f64::consts::PI;

fn almide_rt_math_sqrt(x: f64) -> f64 { x.sqrt() }
fn almide_rt_math_pi() -> f64 { PI }

#[magnus::wrap(class = "AlmideMathlib::Point")]
#[derive(Clone, Debug)]
struct Point { x: f64, y: f64 }

impl Point {
    fn new(x: f64, y: f64) -> Self { Point { x, y } }
    fn x(&self) -> f64 { self.x }
    fn y(&self) -> f64 { self.y }
    fn inspect(&self) -> String { format!("Point(x={}, y={})", self.x, self.y) }
}

#[magnus::wrap(class = "AlmideMathlib::Shape")]
#[derive(Clone, Debug)]
struct Shape { tag: String, v0: f64, v1: f64 }

impl Shape {
    fn circle(r: f64) -> Self { Shape { tag: "Circle".into(), v0: r, v1: 0.0 } }
    fn rect(w: f64, h: f64) -> Self { Shape { tag: "Rect".into(), v0: w, v1: h } }
    fn inspect(&self) -> String {
        if self.tag == "Circle" { format!("Shape::Circle({})", self.v0) }
        else { format!("Shape::Rect({}, {})", self.v0, self.v1) }
    }
}

fn rb_distance(a: &Point, b: &Point) -> f64 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    almide_rt_math_sqrt(dx * dx + dy * dy)
}

fn rb_area(s: &Shape) -> f64 {
    if s.tag == "Circle" { almide_rt_math_pi() * s.v0 * s.v0 }
    else { s.v0 * s.v1 }
}

fn rb_midpoint(a: &Point, b: &Point) -> Point {
    Point { x: (a.x + b.x) / 2.0, y: (a.y + b.y) / 2.0 }
}

fn rb_describe(s: &Shape) -> String {
    if s.tag == "Circle" { format!("circle with radius {}", s.v0) }
    else { format!("rectangle {}x{}", s.v0, s.v1) }
}

#[magnus::init]
fn init(ruby: &Ruby) -> Result<(), Error> {
    let module = ruby.define_module("AlmideMathlib")?;

    let point = module.define_class("Point", ruby.class_object())?;
    point.define_singleton_method("new", function!(Point::new, 2))?;
    point.define_method("x", method!(Point::x, 0))?;
    point.define_method("y", method!(Point::y, 0))?;
    point.define_method("inspect", method!(Point::inspect, 0))?;
    point.define_method("to_s", method!(Point::inspect, 0))?;

    let shape = module.define_class("Shape", ruby.class_object())?;
    shape.define_singleton_method("circle", function!(Shape::circle, 1))?;
    shape.define_singleton_method("rect", function!(Shape::rect, 2))?;
    shape.define_method("inspect", method!(Shape::inspect, 0))?;

    module.define_module_function("distance", function!(rb_distance, 2))?;
    module.define_module_function("area", function!(rb_area, 1))?;
    module.define_module_function("midpoint", function!(rb_midpoint, 2))?;
    module.define_module_function("describe", function!(rb_describe, 1))?;

    Ok(())
}
