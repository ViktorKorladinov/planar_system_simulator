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
    const baseCenter = (CELL_SIZE - MOVER_SIZE) / 2;
    assert(res[0][0].offsetX === 0 && res[0][0].offsetY === 0, 'Loading mover alone has (0, 0) offset at t=0');
    assert(res[0][1].offsetX === 0 && res[0][1].offsetY === 0, 'Loading mover alone has (0, 0) offset at t=1');
    assert(res[0][1].x === 2 * CELL_SIZE + baseCenter, 'Loading mover x is at exact tile center');
    assert(res[0][1].y === 3 * CELL_SIZE + baseCenter, 'Loading mover y is at exact tile center');
  }

  // Test 2: Moving mover in transit drives in right-hand lane
  {
    // Moving East: (dx=1, dy=0) -> SVG normal is (0, 1) -> offset Y is +60
    const pathsEast = [
      [
        { x: 0, y: 0, mode: 'transit' },
        { x: 1, y: 0, mode: 'transit' },
        { x: 2, y: 0, mode: 'transit' },
      ]
    ];
    const resEast = processMoverTrajectories(pathsEast);
    assert(resEast[0][1].offsetX === 0 && resEast[0][1].offsetY === LANE_OFFSET,
      'Eastbound transit mover is shifted South (+Y) by 60px');

    // Moving South: (dx=0, dy=1) -> SVG normal is (-1, 0) -> offset X is -60
    const pathsSouth = [
      [
        { x: 0, y: 0, mode: 'transit' },
        { x: 0, y: 1, mode: 'transit' },
        { x: 0, y: 2, mode: 'transit' },
      ]
    ];
    const resSouth = processMoverTrajectories(pathsSouth);
    assert(resSouth[0][1].offsetX === -LANE_OFFSET && resSouth[0][1].offsetY === 0,
      'Southbound transit mover is shifted West (-X) by 60px');
  }

  // Test 3: Cooperative Yielding ("scoot-aside")
  {
    // Mover 0 is loading at (2, 2)
    // Mover 1 transits East through (2, 2) at t=1
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

    // At t=0: Mover 0 alone at (2, 2) -> offset (0, 0)
    assert(res[0][0].offsetX === 0 && res[0][0].offsetY === 0,
      't=0: Loading mover is at center (0, 0) before transiter arrives');

    // At t=1: Both at (2, 2).
    // Transiter is moving East -> normal is (0, 1) -> offset is (0, +60)
    // Loading mover yields to opposite lane -> offset is (0, -60)
    const loadStep = res[0][1];
    const transStep = res[1][1];

    assert(transStep.offsetY === LANE_OFFSET, 't=1: Transiting mover takes right lane (+60)');
    assert(loadStep.offsetY === -LANE_OFFSET, 't=1: Loading mover scoots to opposite lane (-60)');

    const dist = Math.hypot(transStep.x - loadStep.x, transStep.y - loadStep.y);
    assert(dist >= 120, `t=1: Clearance between movers is ${dist}px (>= 120px > 112px mover size)`);

    // At t=2: Transiter moved to (3, 2). Mover 0 is alone at (2, 2) -> returns to (0, 0)
    assert(res[0][2].offsetX === 0 && res[0][2].offsetY === 0,
      't=2: Loading mover returns to center (0, 0) after transiter leaves');
  }

  // Test 4: Head-on Edge Swapping (A -> B vs B -> A)
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

    // Mover 0 (East): offset Y is +60 at both t=0 and t=1
    // Mover 1 (West): offset Y is -60 at both t=0 and t=1
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
