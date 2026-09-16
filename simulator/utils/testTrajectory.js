import { processMoverTrajectories, CELL_SIZE, MOVER_SIZE, LANE_OFFSET } from './trajectoryProcessor.js';

function runTests() {
  console.log('Running Trajectory Processor Tests...\n');
  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`✓ PASS: ${message}`);
      passed++;
    } else {
      console.error(`✗ FAIL: ${message}`);
      failed++;
    }
  }

  const baseCenter = (CELL_SIZE - MOVER_SIZE) / 2;

  // Test 1: Loading mover alone stays at exact tile center
  {
    const paths = [
      [
        { x: 2, y: 3, mode: 'loading' },
        { x: 2, y: 3, mode: 'loading' },
        { x: 2, y: 3, mode: 'loading' },
      ]
    ];
    const res = processMoverTrajectories(paths);
    assert(res[0][0].offsetX === 0 && res[0][0].offsetY === 0, 'Loading mover alone has (0, 0) offset at t=0');
    assert(res[0][1].offsetX === 0 && res[0][1].offsetY === 0, 'Loading mover alone has (0, 0) offset at t=1');
    assert(res[0][1].x === 2 * CELL_SIZE + baseCenter, 'Loading mover x is at exact tile center');
    assert(res[0][1].y === 3 * CELL_SIZE + baseCenter, 'Loading mover y is at exact tile center');
  }

  // Test 2: Moving mover alone stays at exact tile center
  {
    const pathsEast = [
      [
        { x: 0, y: 0, mode: 'transit' },
        { x: 1, y: 0, mode: 'transit' },
        { x: 2, y: 0, mode: 'transit' },
      ]
    ];
    const resEast = processMoverTrajectories(pathsEast);
    assert(resEast[0][1].offsetX === 0 && resEast[0][1].offsetY === 0,
      'Eastbound transit mover alone stays in center (0, 0)');
    assert(resEast[0][1].y === baseCenter,
      'Eastbound transit mover y is exactly centered along the corridor');
  }

  // Test 3: Cooperative Yielding (Loading vs Transit on same tile)
  {
    const paths = [
      [
        { x: 2, y: 2, mode: 'loading' },
        { x: 2, y: 2, mode: 'loading' },
        { x: 2, y: 2, mode: 'loading' },
      ],
      [
        { x: 1, y: 2, mode: 'transit' },
        { x: 2, y: 2, mode: 'transit' },
        { x: 3, y: 2, mode: 'transit' },
      ]
    ];
    const res = processMoverTrajectories(paths);

    assert(res[0][0].offsetX === 0 && res[0][0].offsetY === 0,
      't=0: Loading mover is at center (0, 0) before transiter arrives');
    assert(res[1][0].offsetX === 0 && res[1][0].offsetY === 0,
      't=0: Transiting mover is at center (0, 0) before reaching shared tile');

    const loadStep = res[0][1];
    const transStep = res[1][1];

    assert(transStep.offsetY === LANE_OFFSET, 't=1: Transiting mover veers to right lane (+60)');
    assert(loadStep.offsetY === -LANE_OFFSET, 't=1: Loading mover scoots to opposite lane (-60)');

    const dist = Math.hypot(transStep.x - loadStep.x, transStep.y - loadStep.y);
    assert(dist >= 120, `t=1: Clearance between movers is ${dist}px (>= 120px > 112px mover size)`);

    assert(res[0][2].offsetX === 0 && res[0][2].offsetY === 0,
      't=2: Loading mover returns to center (0, 0) after transiter leaves');
    assert(res[1][2].offsetX === 0 && res[1][2].offsetY === 0,
      't=2: Transiting mover returns to center (0, 0) once alone');
  }

  // Test 4: TWO TRANSITING MOVERS sharing the SAME tile in opposite directions
  {
    // Mover 0 moves East: (1, 2) -> (2, 2) -> (3, 2)
    // Mover 1 moves West: (3, 2) -> (2, 2) -> (1, 2)
    // Both occupy (2, 2) at t=1!
    const paths = [
      [
        { x: 1, y: 2, mode: 'transit' },
        { x: 2, y: 2, mode: 'transit' },
        { x: 3, y: 2, mode: 'transit' },
      ],
      [
        { x: 3, y: 2, mode: 'transit' },
        { x: 2, y: 2, mode: 'transit' },
        { x: 1, y: 2, mode: 'transit' },
      ]
    ];
    const res = processMoverTrajectories(paths);

    const m0 = res[0][1];
    const m1 = res[1][1];

    assert(m0.offsetY === LANE_OFFSET, 'Two transiting movers on same tile: Eastbound takes South lane (+60)');
    assert(m1.offsetY === -LANE_OFFSET, 'Two transiting movers on same tile: Westbound takes North lane (-60)');

    const dist = Math.hypot(m0.x - m1.x, m0.y - m1.y);
    assert(dist >= 120, `Two transiting movers on same tile have ${dist}px clearance (>= 120px > 112px)`);
  }

  // Test 5: Head-on Edge Swapping (A -> B vs B -> A at the same tick)
  {
    const paths = [
      [
        { x: 0, y: 0, mode: 'transit' },
        { x: 1, y: 0, mode: 'transit' },
      ],
      [
        { x: 1, y: 0, mode: 'transit' },
        { x: 0, y: 0, mode: 'transit' },
      ]
    ];
    const res = processMoverTrajectories(paths);

    assert(res[0][0].offsetY === LANE_OFFSET && res[0][1].offsetY === LANE_OFFSET,
      'Edge swap: Eastbound mover stays in +60 lane');
    assert(res[1][0].offsetY === -LANE_OFFSET && res[1][1].offsetY === -LANE_OFFSET,
      'Edge swap: Westbound mover stays in -60 lane');

    const separationY = Math.abs(res[0][0].y - res[1][0].y);
    assert(separationY === 120, `Edge swap: Continuous lateral clearance is ${separationY}px`);
  }

  console.log(`\nTests finished: ${passed} passed, ${failed} failed.`);
  if (failed > 0) process.exit(1);
}

runTests();
