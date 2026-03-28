use std::f64::consts::PI;

fn almide_rt_math_sqrt(x: f64) -> f64 { x.sqrt() }
fn almide_rt_math_pi() -> f64 { PI }

#[repr(C)]
pub struct Point { pub x: f64, pub y: f64 }

#[repr(C)]
pub struct MidpointResult { pub x: f64, pub y: f64 }

#[no_mangle]
pub extern "C" fn almide_distance(ax: f64, ay: f64, bx: f64, by: f64) -> f64 {
    let dx = ax - bx;
    let dy = ay - by;
    almide_rt_math_sqrt(dx * dx + dy * dy)
}

#[no_mangle]
pub extern "C" fn almide_area_circle(r: f64) -> f64 {
    almide_rt_math_pi() * r * r
}

#[no_mangle]
pub extern "C" fn almide_area_rect(w: f64, h: f64) -> f64 {
    w * h
}

#[no_mangle]
pub extern "C" fn almide_midpoint(ax: f64, ay: f64, bx: f64, by: f64, out: *mut MidpointResult) {
    unsafe {
        (*out).x = (ax + bx) / 2.0;
        (*out).y = (ay + by) / 2.0;
    }
}
