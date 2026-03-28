/**
 * TypeScript wrapper for the Almide mathlib WASM module.
 *
 * Loads mathlib.wasm, stubs all WASI imports, and exposes typed functions
 * that handle memory allocation and data marshalling transparently.
 */

// ---------- Public types ----------

export interface Point {
  x: number;
  y: number;
}

export type Shape =
  | { tag: "Circle"; radius: number }
  | { tag: "Rect"; width: number; height: number };

// ---------- Internals ----------

let memory: WebAssembly.Memory;
let view: DataView;
let alloc: (n: number) => number;
let wasmDistance: (a: number, b: number) => number;
let wasmArea: (s: number) => number;
let wasmMidpoint: (a: number, b: number) => number;
let wasmDescribe: (s: number) => number;

/** Re-acquire the DataView after any call that might grow memory. */
function refreshView(): void {
  view = new DataView(memory.buffer);
}

// ---------- Memory layout helpers ----------

// Point: 16 bytes — [f64 x][f64 y], little-endian
function writePoint(p: Point): number {
  const ptr = alloc(16);
  refreshView();
  view.setFloat64(ptr, p.x, true);
  view.setFloat64(ptr + 8, p.y, true);
  return ptr;
}

function readPoint(ptr: number): Point {
  refreshView();
  return {
    x: view.getFloat64(ptr, true),
    y: view.getFloat64(ptr + 8, true),
  };
}

// Shape (tagged union): [i32 tag][f64 ...payload]
//   Circle (tag 0): 12 bytes — [i32=0][f64 radius]
//   Rect   (tag 1): 20 bytes — [i32=1][f64 width][f64 height]
function writeShape(s: Shape): number {
  if (s.tag === "Circle") {
    const ptr = alloc(12);
    refreshView();
    view.setInt32(ptr, 0, true);
    view.setFloat64(ptr + 4, s.radius, true);
    return ptr;
  } else {
    const ptr = alloc(20);
    refreshView();
    view.setInt32(ptr, 1, true);
    view.setFloat64(ptr + 4, s.width, true);
    view.setFloat64(ptr + 12, s.height, true);
    return ptr;
  }
}

// String: [i32 len][u8... bytes]
function readString(ptr: number): string {
  refreshView();
  const len = view.getInt32(ptr, true);
  const bytes = new Uint8Array(memory.buffer, ptr + 4, len);
  return new TextDecoder().decode(bytes);
}

// ---------- Public API ----------

/** Euclidean distance between two points. */
export function distance(a: Point, b: Point): number {
  return wasmDistance(writePoint(a), writePoint(b));
}

/** Area of a geometric shape. */
export function area(shape: Shape): number {
  return wasmArea(writeShape(shape));
}

/** Midpoint between two points. */
export function midpoint(a: Point, b: Point): Point {
  const resultPtr = wasmMidpoint(writePoint(a), writePoint(b));
  return readPoint(resultPtr);
}

/** Human-readable description of a shape. */
export function describe(shape: Shape): string {
  const strPtr = wasmDescribe(writeShape(shape));
  return readString(strPtr);
}

// ---------- Initialisation ----------

/** Load the WASM module and wire everything up. */
export async function init(wasmPath: string): Promise<void> {
  const bytes = await Deno.readFile(wasmPath);
  const mod = new WebAssembly.Module(bytes);

  // Build import stubs — iterate the module's declared imports so we never
  // miss one, regardless of which WASI functions the binary was linked against.
  const importObject: Record<string, Record<string, WebAssembly.ImportValue>> = {};
  for (const imp of WebAssembly.Module.imports(mod)) {
    if (!importObject[imp.module]) importObject[imp.module] = {};
    if (imp.kind === "function") {
      // Minimal stub: return 0 (ESUCCESS for most WASI calls).
      importObject[imp.module][imp.name] = (..._args: unknown[]) => 0;
    }
  }

  const instance = new WebAssembly.Instance(mod, importObject);
  const ex = instance.exports;

  memory = ex.memory as WebAssembly.Memory;
  alloc = ex.__alloc as (n: number) => number;
  wasmDistance = ex.distance as (a: number, b: number) => number;
  wasmArea = ex.area as (s: number) => number;
  wasmMidpoint = ex.midpoint as (a: number, b: number) => number;
  wasmDescribe = ex.describe as (s: number) => number;

  refreshView();
}
