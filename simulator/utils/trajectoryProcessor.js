/**
 * Trajectory Post-Processor for Multi-Mover Grid Simulation
 *
 * Implements:
 * 1. Exact tile centering for loading/dispensing movers.
 * 2. Right-hand drive (+lane offset) for transit movers to prevent head-on collisions.
 * 3. Cooperative yielding ("scoot-aside") when a transit mover passes through a tile
 *    where another mover is loading/dispensing.
 * 4. Comprehensive dual-transit conflict resolution (opposite, same, and perpendicular directions).
 * 5. Head-on edge swap corridor clearance preservation.
 * 6. Preservation of rest offsets for wait_rest movers.
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
      let isTurning = false;
      if (isMoving && mode !== 'wait_rest') {
        const inNorm = getRightHandNormal(inDx, inDy);
        const outNorm = getRightHandNormal(outDx, outDy);

        if ((inDx !== 0 || inDy !== 0) && (outDx !== 0 || outDy !== 0)) {
          if (inNorm.nx !== outNorm.nx || inNorm.ny !== outNorm.ny) {
            // Turning through waypoint: outer corner is intersection of incoming and outgoing lanes
            nx = inNorm.nx + outNorm.nx;
            ny = inNorm.ny + outNorm.ny;
            isTurning = true;
          } else {
            // Continuing straight along same lane
            nx = inNorm.nx;
            ny = inNorm.ny;
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
        // Moving traffic drives on right-hand lane (or outer corner if turning)
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
        inDx,
        inDy,
        outDx,
        outDy,
        isMoving,
        isTurning,
        mode,
        moverIdx,
      };
    });
  });

  // Step 2: Same-Tile Conflict Resolution Pre-pass
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

      const transiting = occupants.filter(s => s.isMoving && s.mode !== 'loading');
      const loading = occupants.filter(s => s.mode === 'loading' || !s.isMoving);

      // Case A: 1 transiting mover and 1 (or more) loading/stopped movers
      if (transiting.length >= 1 && loading.length >= 1) {
        const trans = transiting[0];
        // Transiting mover takes its right-hand lane
        trans.offsetX = trans.nx * LANE_OFFSET;
        trans.offsetY = trans.ny * LANE_OFFSET;

        // Loading mover yields to the opposite lane
        const load = loading[0];
        if (Math.abs(trans.nx) > 0.001 || Math.abs(trans.ny) > 0.001) {
          load.offsetX = -trans.nx * LANE_OFFSET;
          load.offsetY = -trans.ny * LANE_OFFSET;
        } else {
          load.offsetX = -LANE_OFFSET;
          load.offsetY = 0;
        }
      }
      // Case B: 2 or more loading movers on the same tile
      else if (loading.length >= 2 && transiting.length === 0) {
        loading[0].offsetX = -LANE_OFFSET;
        loading[0].offsetY = 0;
        loading[1].offsetX = LANE_OFFSET;
        loading[1].offsetY = 0;
      }
      // Case C: 2 transiting movers on the same tile
      else if (transiting.length >= 2) {
        const t1 = transiting[0];
        const t2 = transiting[1];

        // Check if opposite directions
        const dotProd = t1.nx * t2.nx + t1.ny * t2.ny;
        if (dotProd < -0.5) {
          // Opposite directions: each keeps its own right-hand lane
          t1.offsetX = t1.nx * LANE_OFFSET;
          t1.offsetY = t1.ny * LANE_OFFSET;
          t2.offsetX = t2.nx * LANE_OFFSET;
          t2.offsetY = t2.ny * LANE_OFFSET;
        } else if (dotProd > 0.5) {
          // Same direction: split into parallel lanes (Lane 1 and Lane 0)
          t1.offsetX = t1.nx * LANE_OFFSET;
          t1.offsetY = t1.ny * LANE_OFFSET;
          t2.offsetX = -t1.nx * LANE_OFFSET;
          t2.offsetY = -t1.ny * LANE_OFFSET;
        } else {
          // Perpendicular crossing: assign opposing diagonal quadrants for 170px clearance
          t1.offsetX = LANE_OFFSET;
          t1.offsetY = LANE_OFFSET;
          t2.offsetX = -LANE_OFFSET;
          t2.offsetY = -LANE_OFFSET;
        }
      }
    }
  }

  // Step 3: Edge-Swap Passing (Head-on: A -> B vs B -> A between adjacent tiles)
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
          // Shift both into right-hand passing lanes throughout the swap
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
