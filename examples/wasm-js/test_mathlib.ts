/**
 * End-to-end test: Almide mathlib WASM -> TypeScript wrapper -> Deno runtime.
 *
 * Exercises every exported function through the typed wrapper.
 */

import {
  init,
  distance,
  area,
  midpoint,
  describe,
  type Point,
  type Shape,
} from "./almide_mathlib.ts";

// ---- Helpers ----

let passed = 0;
let failed = 0;

function assertClose(actual: number, expected: number, label: string, eps = 1e-6): void {
  if (Math.abs(actual - expected) < eps) {
    console.log(`  PASS  ${label}: ${actual}`);
    passed++;
  } else {
    console.log(`  FAIL  ${label}: expected ${expected}, got ${actual}`);
    failed++;
  }
}

function assertEqual<T>(actual: T, expected: T, label: string): void {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) {
    console.log(`  PASS  ${label}: ${JSON.stringify(actual)}`);
    passed++;
  } else {
    console.log(`  FAIL  ${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    failed++;
  }
}

// ---- Tests ----

const wasmPath = new URL("../mathlib.wasm", import.meta.url).pathname;
await init(wasmPath);

console.log("--- distance ---");
assertClose(distance({ x: 0, y: 0 }, { x: 3, y: 4 }), 5.0, "origin to (3,4)");
assertClose(distance({ x: 1, y: 1 }, { x: 1, y: 1 }), 0.0, "same point");
assertClose(distance({ x: -1, y: -1 }, { x: 2, y: 3 }), 5.0, "negative coords");
assertClose(distance({ x: 0, y: 0 }, { x: 1, y: 0 }), 1.0, "unit horizontal");

console.log("--- area ---");
assertClose(area({ tag: "Circle", radius: 5.0 }), Math.PI * 25, "circle r=5");
assertClose(area({ tag: "Circle", radius: 1.0 }), Math.PI, "circle r=1");
assertClose(area({ tag: "Circle", radius: 0.0 }), 0.0, "circle r=0");
assertClose(area({ tag: "Rect", width: 3.0, height: 4.0 }), 12.0, "rect 3x4");
assertClose(area({ tag: "Rect", width: 10.0, height: 0.5 }), 5.0, "rect 10x0.5");

console.log("--- midpoint ---");
assertEqual(midpoint({ x: 0, y: 0 }, { x: 4, y: 6 }), { x: 2, y: 3 }, "(0,0)-(4,6)");
assertEqual(midpoint({ x: -2, y: -2 }, { x: 2, y: 2 }), { x: 0, y: 0 }, "(-2,-2)-(2,2)");
assertEqual(midpoint({ x: 1, y: 1 }, { x: 1, y: 1 }), { x: 1, y: 1 }, "same point");

console.log("--- describe ---");
assertEqual(describe({ tag: "Circle", radius: 5.0 }), "circle with radius 5.0", "circle desc");
assertEqual(describe({ tag: "Rect", width: 3.0, height: 4.0 }), "rectangle 3.0x4.0", "rect desc");

// ---- Summary ----

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) Deno.exit(1);
