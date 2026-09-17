import { processMoverTrajectories, CELL_SIZE, MOVER_SIZE } from './trajectoryProcessor.js';

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
      ]
    ];
    const res = processMoverTrajectories(paths);
    assert(res[0][0].offsetX === 0 && res[0][0].offsetY === 0, 'Loading mover alone has (0, 0) offset at t=0');
    assert(res[0][0].x === 2 * CELL_SIZE + baseCenter, 'Loading mover x is at exact tile center');
    assert(res[0][0].y === 3 * CELL_SIZE + baseCenter, 'Loading mover y is at exact tile center');
    assert(res[0][0].stackCount === 1, 'Alone mover has stackCount = 1');
  }

  // Test 2: Transit mover alone moves straight through tile center
  {
    const paths = [
      [
        { x: 0, y: 0, mode: 'transit' },
        { x: 1, y: 0, mode: 'transit' },
        { x: 2, y: 0, mode: 'transit' },
      ]
    ];
    const res = processMoverTrajectories(paths);
    assert(res[0][1].offsetX === 0 && res[0][1].offsetY === 0, 'Transit mover alone moves through exact center');
    assert(res[0][1].x === 1 * CELL_SIZE + baseCenter, 'Transit mover x is at tile center');
    assert(res[0][1].y === 0 * CELL_SIZE + baseCenter, 'Transit mover y is at tile center');
    assert(res[0][1].stackCount === 1, 'Transit mover alone has stackCount = 1');
  }

  // Test 3: Multiple movers sharing a tile get stacked card offset and stackCount = 2
  {
    const paths = [
      [
        { x: 2, y: 2, mode: 'loading' },
      ],
      [
        { x: 2, y: 2, mode: 'transit' },
      ]
    ];
    const res = processMoverTrajectories(paths);
    const m0 = res[0][0];
    const m1 = res[1][0];

    assert(m0.stackCount === 2 && m1.stackCount === 2, 'Both movers on same tile have stackCount = 2');
    assert(m0.stackIdx === 0 && m1.stackIdx === 1, 'Movers have stackIdx 0 and 1');
    assert(m0.offsetX === -4 && m0.offsetY === 4, 'Mover 0 has bottom-sheet stack offset (-4, +4)');
    assert(m1.offsetX === 4 && m1.offsetY === -4, 'Mover 1 has top-sheet stack offset (+4, -4)');

    const visualOffset = Math.hypot(m0.x - m1.x, m0.y - m1.y);
    assert(Math.round(visualOffset) === 11, `Slight stack shift is ${visualOffset.toFixed(1)}px so both are visible`);
  }

  // Test 4: Rest sites preserve custom rest offsets
  {
    const paths = [
      [
        { x: 1, y: 1, mode: 'wait_rest', rest_offset_x: 1, rest_offset_y: 0 },
      ]
    ];
    const res = processMoverTrajectories(paths);
    assert(res[0][0].offsetX === CELL_SIZE / 2, 'wait_rest preserves rest_offset_x');
    assert(res[0][0].offsetY === 0, 'wait_rest preserves rest_offset_y');
  }

  console.log(`\nTests finished: ${passed} passed, ${failed} failed.`);
  if (failed > 0) process.exit(1);
}

runTests();
