// Almide mathlib — UniFFI bindings (auto-generated from interface.json)

use std::f64::consts::PI;

// ── Almide runtime (minimal subset) ──

fn almide_rt_math_sqrt(x: f64) -> f64 { x.sqrt() }
fn almide_rt_math_pi() -> f64 { PI }

// ── Types ──

#[derive(Debug, Clone, uniffi::Record)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[derive(Debug, Clone, uniffi::Enum)]
pub enum Shape {
    Circle { radius: f64 },
    Rect { width: f64, height: f64 },
}

// ── Functions ──

#[uniffi::export]
pub fn distance(a: &Point, b: &Point) -> f64 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    almide_rt_math_sqrt(dx * dx + dy * dy)
}

#[uniffi::export]
pub fn area(shape: &Shape) -> f64 {
    match shape {
        Shape::Circle { radius: r } => almide_rt_math_pi() * r * r,
        Shape::Rect { width: w, height: h } => w * h,
    }
}

#[uniffi::export]
pub fn midpoint(a: &Point, b: &Point) -> Point {
    Point {
        x: (a.x + b.x) / 2.0,
        y: (a.y + b.y) / 2.0,
    }
}

#[uniffi::export]
pub fn describe(shape: &Shape) -> String {
    match shape {
        Shape::Circle { radius: r } => format!("circle with radius {}", r),
        Shape::Rect { width: w, height: h } => format!("rectangle {}x{}", w, h),
    }
}

uniffi::setup_scaffolding!();
