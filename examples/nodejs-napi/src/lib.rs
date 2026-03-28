#![allow(unused_parens, unused_variables, dead_code, unused_imports, unused_mut, unused_must_use)]

use napi_derive::napi;

// ---------------------------------------------------------------------------
// Almide runtime (inlined from codegen)
// ---------------------------------------------------------------------------


trait AlmideConcat<Rhs> { type Output; fn concat(self, rhs: Rhs) -> Self::Output; }
impl AlmideConcat<String> for String { type Output = String; #[inline(always)] fn concat(self, rhs: String) -> String { format!("{}{}", self, rhs) } }
impl AlmideConcat<&str> for String { type Output = String; #[inline(always)] fn concat(self, rhs: &str) -> String { format!("{}{}", self, rhs) } }
impl AlmideConcat<String> for &str { type Output = String; #[inline(always)] fn concat(self, rhs: String) -> String { format!("{}{}", self, rhs) } }
impl AlmideConcat<&str> for &str { type Output = String; #[inline(always)] fn concat(self, rhs: &str) -> String { format!("{}{}", self, rhs) } }
impl<T: Clone> AlmideConcat<Vec<T>> for Vec<T> { type Output = Vec<T>; #[inline(always)] fn concat(self, rhs: Vec<T>) -> Vec<T> { let mut r = self; r.extend(rhs); r } }
macro_rules! almide_eq { ($a:expr, $b:expr) => { ($a) == ($b) }; }
macro_rules! almide_ne { ($a:expr, $b:expr) => { ($a) != ($b) }; }
// math extern — Rust native implementations

// Trigonometry
#[inline(always)] pub fn almide_rt_math_sin(x: f64) -> f64 { x.sin() }
#[inline(always)] pub fn almide_rt_math_cos(x: f64) -> f64 { x.cos() }
#[inline(always)] pub fn almide_rt_math_tan(x: f64) -> f64 { x.tan() }
#[inline(always)] pub fn almide_rt_math_asin(x: f64) -> f64 { x.asin() }
#[inline(always)] pub fn almide_rt_math_acos(x: f64) -> f64 { x.acos() }
#[inline(always)] pub fn almide_rt_math_atan(x: f64) -> f64 { x.atan() }
#[inline(always)] pub fn almide_rt_math_atan2(y: f64, x: f64) -> f64 { y.atan2(x) }

// Logarithms / exponentials
#[inline(always)] pub fn almide_rt_math_log(x: f64) -> f64 { x.ln() }
#[inline(always)] pub fn almide_rt_math_log2(x: f64) -> f64 { x.log2() }
#[inline(always)] pub fn almide_rt_math_log10(x: f64) -> f64 { x.log10() }
#[inline(always)] pub fn almide_rt_math_exp(x: f64) -> f64 { x.exp() }
#[inline(always)] pub fn almide_rt_math_pow(base: i64, exp: i64) -> i64 { base.pow(exp as u32) }

// Rounding
#[inline(always)] pub fn almide_rt_math_abs(x: i64) -> i64 { x.abs() }
#[inline(always)] pub fn almide_rt_math_ceil(x: f64) -> f64 { x.ceil() }
#[inline(always)] pub fn almide_rt_math_floor(x: f64) -> f64 { x.floor() }
#[inline(always)] pub fn almide_rt_math_round(x: f64) -> f64 { x.round() }
#[inline(always)] pub fn almide_rt_math_sqrt(x: f64) -> f64 { x.sqrt() }

// Constants
#[inline(always)] pub fn almide_rt_math_pi() -> f64 { std::f64::consts::PI }
#[inline(always)] pub fn almide_rt_math_e() -> f64 { std::f64::consts::E }
#[inline(always)] pub fn almide_rt_math_inf() -> f64 { f64::INFINITY }
#[inline(always)] pub fn almide_rt_math_is_nan(x: f64) -> bool { x.is_nan() }

// Int min/max/sign
#[inline(always)] pub fn almide_rt_math_min(a: i64, b: i64) -> i64 { a.min(b) }
#[inline(always)] pub fn almide_rt_math_max(a: i64, b: i64) -> i64 { a.max(b) }
#[inline(always)] pub fn almide_rt_math_sign(n: i64) -> i64 { if n > 0 { 1 } else if n < 0 { -1 } else { 0 } }

// Float min/max
#[inline(always)] pub fn almide_rt_math_fmin(a: f64, b: f64) -> f64 { a.min(b) }
#[inline(always)] pub fn almide_rt_math_fmax(a: f64, b: f64) -> f64 { a.max(b) }
#[inline(always)] pub fn almide_rt_math_fpow(base: f64, exp: f64) -> f64 { base.powf(exp) }

// Factorial / combinatorics
pub fn almide_rt_math_factorial(n: i64) -> i64 {
    (1..=n).product()
}
pub fn almide_rt_math_choose(n: i64, k: i64) -> i64 {
    if k < 0 || k > n { return 0; }
    let k = k.min(n - k) as u64;
    let mut result: u64 = 1;
    for i in 0..k {
        result = result * (n as u64 - i) / (i + 1);
    }
    result as i64
}
pub fn almide_rt_math_log_gamma(x: f64) -> f64 {
    // Stirling approximation
    let t = x + 6.5;
    (2.5066282746310005_f64).ln()
        + (x - 0.5) * t.ln()
        - t
        + (1.000000000190015
            + 76.18009172947146 / x
            + -86.50532032941677 / (x + 1.0)
            + 24.01409824083091 / (x + 2.0)
            + -1.231739572450155 / (x + 3.0)
            + 0.001208650973866179 / (x + 4.0)
            + -0.000005395239384953 / (x + 5.0))
            .ln()
}

// ---------------------------------------------------------------------------
// Almide-generated types (adapted for napi)
// ---------------------------------------------------------------------------

/// A 2D point with x and y coordinates.
/// napi(object) makes this a plain JS object.
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

/// A geometric shape.
#[napi]
pub struct Shape {
    inner: ShapeInner,
}

#[napi]
impl Shape {
    /// Create a circle.
    #[napi(factory)]
    pub fn circle(v0: f64) -> Shape {
        Shape {
            inner: ShapeInner::Circle(v0),
        }
    }

    /// Create a rect.
    #[napi(factory)]
    pub fn rect(v0: f64, v1: f64) -> Shape {
        Shape {
            inner: ShapeInner::Rect(v0, v1),
        }
    }

}

// ---------------------------------------------------------------------------
// Almide-generated functions (wrapped for napi)
// ---------------------------------------------------------------------------

/// Euclidean distance between two points.
#[napi]
pub fn distance(a: Point, b: Point) -> f64 {
    let dx: f64 = (a.clone().x - b.clone().x);
    let dy: f64 = (a.clone().y - b.clone().y);
    almide_rt_math_sqrt(((dx * dx) + (dy * dy)))
}

/// Area of a geometric shape.
#[napi]
pub fn area(shape: &Shape) -> f64 {
    match shape.inner.clone() { ShapeInner::Circle(r) => ((almide_rt_math_pi() * r) * r),
    ShapeInner::Rect(w, h) => (w * h), }
}

/// Midpoint between two points.
#[napi]
pub fn midpoint(a: Point, b: Point) -> Point {
    Point { x: ((a.clone().x + b.clone().x) / 2f64), y: ((a.clone().y + b.clone().y) / 2f64) }
}

/// Human-readable description of a shape.
#[napi]
pub fn describe(shape: &Shape) -> String {
    match shape.inner.clone() { ShapeInner::Circle(r) => format!("circle with radius {}", r),
    ShapeInner::Rect(w, h) => format!("rectangle {}x{}", w, h), }
}
