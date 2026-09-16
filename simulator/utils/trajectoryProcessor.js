/**
 * Trajectory Post-Processor for Multi-Mover Grid Simulation
 *
 * Design:
 * 1. By default, ALL movers (both loading and transit) travel strictly down the EXACT CENTER
 *    of tiles (offset = (0, 0)). This prevents wall-hugging, diagonal crab-walking, and speed disparities.
 * 2. Cooperative Yielding ("Scoot-Aside"):
 *    When a transit mover passes through a tile where another mover is loading/dispensing at tick t:
 *    - The transit mover takes its right-hand lane (+60px * n).
 *    - The loading mover cooperatively scoots to the opposite lane (-60px * n).
 *    - Center-to-center distance is 120px > 112px mover width (zero collision, 8px clearance).
 *    - At tick t+1, when the transiter exits, the loading mover smoothly returns to center (0, 0).
 * 3. Edge-Swap Collision Avoidance:
 *    When two movers pass each other head-on along the same edge (A -> B vs B -> A at the same tick),
 *    they veer into their respective right-hand lanes during the transit to pass safely.
 * 4. Preservation of rest offsets for wait_rest movers.
 */

export const CELL_SIZE = 240;
export const MOVER_SIZE = 112;
export const LANE_OFFSET = 60; // CELL_SIZE / 4

/**
 * Returns SVG right-hand normal vector for movement vector (dx, dy).
 * In SVG coordinates, +X is right and +Y is down.
 * A 90-degree clockwise rotation converts (dx, dy) into (-dy, dx).
 */
export function getRightHandNormal(dx, dy) {
  if (dx === 0 && dy === 0) return { nx: 0, ny: 0 };
  const length = Math.hypot(dx, dy);
  return {
    nx: -dy / length,
    ny: dx / length,
  };
}

/**
 * Processes raw simulation paths into exact pixel coordinates with smooth cooperative yields.
 *
 * @param {Array<Array<Object>>} allPaths - Array of mover paths from simulationData
 * @returns {Array<Array<Object>>} Processed paths with calculated x, y, logicalX, logicalY
 */
export function processMoverTrajectories(allPaths) {
  if (!allPaths || allPaths.length === 0) return [];

  const numMovers = allPaths.length;
  const numSteps = allPaths[0].length;
  const baseCenterOffset = (CELL_SIZE - MOVER_SIZE) / 2;

  // Step 1: Initial pass - compute base geometry, headings, and default center offsets
  const processed = allPaths.map((path, moverIdx) => {
    return path.map((step, t) => {
      const logicalX = step.x;
      const logicalY = step.y;
      const mode = step.mode;

      // Determine transit vectors (incoming and outgoing)
      let inDx = 0, inDy = 0;
      let outDx = 0, outDy = 0;

      if (t > 0) {
        const prev = path[t - 1];
        inDx = logicalX - prev.x;
        inDy = logicalY - prev.y;
      }

      if (t < numSteps - 1) {
        const next = path[t + 1];
        outDx = next.x - logicalX;
        outDy = next.y - logicalY;
      }

      const isMoving = inDx !== 0 || inDy !== 0 || outDx !== 0 || outDy !== 0;

      // Determine movement normal
      let nx = 0, ny = 0;
      if (isMoving && mode !== 'wait_rest') {
        const outNorm = getRightHandNormal(outDx, outDy);
        const inNorm = getRightHandNormal(inDx, inDy);

        if (outDx !== 0 || outDy !== 0) {
          nx = outNorm.nx;
          ny = outNorm.ny;
        } else if (inDx !== 0 || inDy !== 0) {
          nx = inNorm.nx;
          ny = inNorm.ny;
        }
      }

      let offsetX = 0;
      let offsetY = 0;

      if (mode === 'wait_rest') {
        offsetX = (step.rest_offset_x || 0) * (CELL_SIZE / 2);
        offsetY = (step.rest_offset_y || 0) * (CELL_SIZE / 2);
      } else {
        // By default, ALL movers travel dead-center to avoid diagonal drift & wall-hugging
        offsetX = 0;
        offsetY = 0;
      }

      return {
        ...step,
        logicalX,
        logicalY,
        baseX: logicalX * CELL_SIZE + baseCenterOffset,
        baseY: logicalY * CELL_SIZE + baseCenterOffset,
        offsetX,
        offsetY,
        nx,
        ny,
        isMoving,
        mode,
        moverIdx,
      };
    });
  });

  // Step 2: Cooperative Yielding on Shared Tiles
  // Check each tick for tiles containing a loading/stationary mover and a passing mover
  for (let t = 0; t < numSteps; t++) {
    const tileOccupants = new Map();

    for (let m = 0; m < numMovers; m++) {
      const step = processed[m][t];
      if (step.mode === 'wait_rest') continue;

      const key = `${step.logicalX},${step.logicalY}`;
      if (!tileOccupants.has(key)) {
        tileOccupants.set(key, []);
      }
      tileOccupants.get(key).push(step);
    }

    for (const [key, occupants] of tileOccupants.entries()) {
      if (occupants.length < 2) continue;

      const transiting = occupants.find(s => s.isMoving && s.mode !== 'loading');
      const loading = occupants.find(s => s.mode === 'loading' || !s.isMoving);

      if (transiting && loading) {
        // Moving mover takes its right-hand lane (+nx, +ny)
        transiting.offsetX = transiting.nx * LANE_OFFSET;
        transiting.offsetY = transiting.ny * LANE_OFFSET;

        // Loading mover yields to opposite lane (-nx, -ny)
        if (Math.abs(transiting.nx) > 0.001 || Math.abs(transiting.ny) > 0.001) {
          loading.offsetX = -transiting.nx * LANE_OFFSET;
          loading.offsetY = -transiting.ny * LANE_OFFSET;
        } else {
          loading.offsetX = -LANE_OFFSET;
        }
      } else if (occupants.length === 2 && occupants.every(s => s.mode === 'loading')) {
        occupants[0].offsetX = -LANE_OFFSET;
        occupants[1].offsetX = LANE_OFFSET;
      }
    }
  }

  // Step 3: Edge-Swap Passing (Head-on: A -> B vs B -> A at the same tick)
  for (let t = 0; t < numSteps - 1; t++) {
    for (let m1 = 0; m1 < numMovers; m1++) {
      const s1 = processed[m1][t];
      const next1 = processed[m1][t + 1];
      if (!s1.isMoving) continue;

      for (let m2 = m1 + 1; m2 < numMovers; m2++) {
        const s2 = processed[m2][t];
        const next2 = processed[m2][t + 1];
        if (!s2.isMoving) continue;

        // Check if swapping adjacent tiles
        if (s1.logicalX === next2.logicalX && s1.logicalY === next2.logicalY &&
            next1.logicalX === s2.logicalX && next1.logicalY === s2.logicalY) {
          // Shift both into right-hand passing lanes during the swap
          s1.offsetX = s1.nx * LANE_OFFSET;
          s1.offsetY = s1.ny * LANE_OFFSET;
          s2.offsetX = s2.nx * LANE_OFFSET;
          s2.offsetY = s2.ny * LANE_OFFSET;
          next1.offsetX = s1.nx * LANE_OFFSET;
          next1.offsetY = s1.ny * LANE_OFFSET;
          next2.offsetX = s2.nx * LANE_OFFSET;
          next2.offsetY = s2.ny * LANE_OFFSET;
        }
      }
    }
  }

  // Step 4: Compute final pixel coordinates (x, y)
  for (let m = 0; m < numMovers; m++) {
    for (let t = 0; t < numSteps; t++) {
      const step = processed[m][t];
      step.x = step.baseX + step.offsetX;
      step.y = step.baseY + step.offsetY;
    }
  }

  return processed;
}
