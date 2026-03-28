const { distance, area, midpoint, describe, Shape } = require('./index.js');

const d = distance({x: 0, y: 0}, {x: 3, y: 4});
console.log(`distance = ${d}`);
console.assert(Math.abs(d - 5.0) < 0.001);

const mid = midpoint({x: 0, y: 0}, {x: 10, y: 10});
console.log(`midpoint = (${mid.x}, ${mid.y})`);
console.assert(Math.abs(mid.x - 5.0) < 0.001);

const c = Shape.circle(5.0);
const a = area(c);
console.log(`area(circle(5)) = ${a}`);
console.assert(Math.abs(a - 78.54) < 0.1);

const r = Shape.rect(3.0, 4.0);
console.log(`area(rect(3,4)) = ${area(r)}`);
console.assert(Math.abs(area(r) - 12.0) < 0.001);

console.log(`describe(circle) = ${describe(c)}`);
console.log(`describe(rect) = ${describe(r)}`);

console.log('\nNode.js napi-rs: ALL TESTS PASSED');
