#![allow(unused_parens, unused_variables, dead_code, unused_imports, unused_mut, unused_must_use)]

use napi_derive::napi;

// ---------------------------------------------------------------------------
// Almide math runtime (inlined from codegen)
// ---------------------------------------------------------------------------

#[inline(always)]
fn almide_rt_math_sqrt(x: f64) -> f64 {
    x.sqrt()
}

#[inline(always)]
fn almide_rt_math_pi() -> f64 {
    std::f64::consts::PI
}

// ---------------------------------------------------------------------------
// Almide-generated types (adapted for napi)
// ---------------------------------------------------------------------------

/// A 2D point with x and y coordinates.
/// napi(object) makes this a plain JS object { x: number, y: number }.
#[napi(object)]
#[derive(Clone, Debug)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

/// Internal Rust enum for Shape -- not directly exposed to JS.
#[derive(Clone, Debug)]
enum ShapeInner {
    Circle(f64),
    Rect(f64, f64),
}

/// A geometric shape, exposed as a napi class with factory methods.
#[napi]
pub struct Shape {
    inner: ShapeInner,
}

#[napi]
impl Shape {
    /// Create a circle with the given radius.
    #[napi(factory)]
    pub fn circle(radius: f64) -> Shape {
        Shape {
            inner: ShapeInner::Circle(radius),
        }
    }

    /// Create a rectangle with the given width and height.
    #[napi(factory)]
    pub fn rect(width: f64, height: f64) -> Shape {
        Shape {
            inner: ShapeInner::Rect(width, height),
        }
    }
}

// ---------------------------------------------------------------------------
// Almide-generated functions (wrapped for napi)
// ---------------------------------------------------------------------------

/// Euclidean distance between two points.
#[napi]
pub fn distance(a: Point, b: Point) -> f64 {
    let dx: f64 = a.x - b.x;
    let dy: f64 = a.y - b.y;
    almide_rt_math_sqrt((dx * dx) + (dy * dy))
}

/// Area of a geometric shape.
#[napi]
pub fn area(shape: &Shape) -> f64 {
    match &shape.inner {
        ShapeInner::Circle(r) => (almide_rt_math_pi() * r) * r,
        ShapeInner::Rect(w, h) => w * h,
    }
}

/// Midpoint between two points.
#[napi]
pub fn midpoint(a: Point, b: Point) -> Point {
    Point {
        x: (a.x + b.x) / 2.0,
        y: (a.y + b.y) / 2.0,
    }
}

/// Human-readable description of a shape.
#[napi]
pub fn describe(shape: &Shape) -> String {
    match &shape.inner {
        ShapeInner::Circle(r) => format!("circle with radius {}", r),
        ShapeInner::Rect(w, h) => format!("rectangle {}x{}", w, h),
    }
}
