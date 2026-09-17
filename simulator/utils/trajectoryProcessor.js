/**
 * Trajectory Post-Processor for Multi-Mover Grid Simulation
 *
 * Implements:
 * 1. Exact tile centering for loading/dispensing movers.
 * 2. Right-hand drive (+lane offset) for transit movers to prevent head-on collisions.
 * 3. Cooperative yielding ("scoot-aside") when a transit mover passes through a tile
 *    where another mover is loading/dispensing.
 * 4. Preservation of rest offsets for wait_rest movers.
 */

export const CELL_SIZE = 240;
export const MOVER_SIZE = 112;
export const LANE_OFFSET = 60; // CELL_SIZE / 4: provides 120px center-to-center clearance (> 112px mover width)

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
 * Processes raw simulation paths into exact pixel coordinates with lane offsets and cooperative yields.
 *
 * @param {Array<Array<Object>>} allPaths - Array of mover paths from simulationData
 * @returns {Array<Array<Object>>} Processed paths with calculated x, y, logicalX, logicalY
 */
export function processMoverTrajectories(allPaths) {
  if (!allPaths || allPaths.length === 0) return [];

  const numMovers = allPaths.length;
  const numSteps = allPaths[0].length;
  const baseCenterOffset = (CELL_SIZE - MOVER_SIZE) / 2;

  // Step 1: Initial pass - calculate base geometry, directions, and baseline lane offsets
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

      // Calculate effective normal for moving traffic
      let nx = 0, ny = 0;
      if (isMoving && mode !== 'wait_rest') {
        const inNorm = getRightHandNormal(inDx, inDy);
        const outNorm = getRightHandNormal(outDx, outDy);

        if ((inDx !== 0 || inDy !== 0) && (outDx !== 0 || outDy !== 0)) {
          // Turning or continuing transit through waypoint
          nx = inNorm.nx + outNorm.nx;
          ny = inNorm.ny + outNorm.ny;
          const mag = Math.hypot(nx, ny);
          if (mag > 0.001) {
            nx = (nx / mag);
            ny = (ny / mag);
          }
        } else if (outDx !== 0 || outDy !== 0) {
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
      } else if (mode === 'loading') {
        // Loading movers default to exact center
        offsetX = 0;
        offsetY = 0;
      } else if (isMoving) {
        // Moving traffic drives on the right-hand lane
        offsetX = nx * LANE_OFFSET;
        offsetY = ny * LANE_OFFSET;
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

  // Step 2: Cooperative Yielding Pre-pass
  // Check each tick for tiles containing a loading/stationary mover and a passing mover
  for (let t = 0; t < numSteps; t++) {
    const tileOccupants = new Map();

    for (let m = 0; m < numMovers; m++) {
      const step = processed[m][t];
      if (step.mode === 'wait_rest') continue; // Wait rest has dedicated rest spots

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

        // If the transiting normal is non-zero, scoot loading mover to opposite side
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

  // Step 3: Compute final pixel coordinates (x, y)
  for (let m = 0; m < numMovers; m++) {
    for (let t = 0; t < numSteps; t++) {
      const step = processed[m][t];
      step.x = step.baseX + step.offsetX;
      step.y = step.baseY + step.offsetY;
    }
  }

  return processed;
}
