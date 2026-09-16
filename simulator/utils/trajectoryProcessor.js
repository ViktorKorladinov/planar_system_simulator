/**
 * Trajectory Post-Processor for Multi-Mover Grid Simulation
 *
 * Design:
 * 1. By default, ALL movers travel down the EXACT CENTER of tiles (offset = (0, 0))
 *    when traveling alone, avoiding wall-hugging and diagonal drifting.
 * 2. Shared-Tile Collision Avoidance:
 *    When 2 movers occupy the SAME tile at tick t:
 *    - One loading/stationary + one transiting: loading scoots aside (-60px * n), transiting takes right lane (+60px * n).
 *    - Two transiting movers (opposite directions): each takes its respective right lane (+60px * n1, +60px * n2), separated by 120px.
 *    - Two transiting movers (same direction or perpendicular): split to opposite sides with >= 120px clearance.
 *    - Two loading movers: split laterally.
 * 3. Edge-Swap Passing (Head-on passing between adjacent tiles: A -> B vs B -> A at tick t -> t+1):
 *    - Both movers shift into their opposing lateral lanes throughout the transition.
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
        // By default, ALL movers travel dead-center when alone
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
        inDx,
        inDy,
        outDx,
        outDy,
        isMoving,
        mode,
        moverIdx,
      };
    });
  });

  // Step 2: Shared-Tile Collision Avoidance
  // Check each tick for any tile containing multiple movers (loading vs transit, transit vs transit, etc.)
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

      const transiting = occupants.filter(s => s.isMoving);
      const stationary = occupants.filter(s => !s.isMoving);

      if (transiting.length === 1 && stationary.length >= 1) {
        // One transiting, one stationary/loading (cooperative scoot-aside)
        const tr = transiting[0];
        const st = stationary[0];
        tr.offsetX = tr.nx * LANE_OFFSET;
        tr.offsetY = tr.ny * LANE_OFFSET;

        if (Math.abs(tr.nx) > 0.001 || Math.abs(tr.ny) > 0.001) {
          st.offsetX = -tr.nx * LANE_OFFSET;
          st.offsetY = -tr.ny * LANE_OFFSET;
        } else {
          st.offsetX = -LANE_OFFSET;
        }
      } else if (transiting.length >= 2) {
        // TWO (or more) MOVERS ARE BOTH TRANSITING ON THE SAME TILE!
        const m1 = transiting[0];
        const m2 = transiting[1];

        // Check relative directions using dot product of normals
        const dot = m1.nx * m2.nx + m1.ny * m2.ny;
        if (dot < -0.3) {
          // Opposite directions (e.g. East vs West or North vs South):
          // Each takes its own right-hand normal!
          m1.offsetX = m1.nx * LANE_OFFSET;
          m1.offsetY = m1.ny * LANE_OFFSET;
          m2.offsetX = m2.nx * LANE_OFFSET;
          m2.offsetY = m2.ny * LANE_OFFSET;
        } else if (dot > 0.3) {
          // Same direction: split left and right along m1's normal
          m1.offsetX = m1.nx * LANE_OFFSET;
          m1.offsetY = m1.ny * LANE_OFFSET;
          m2.offsetX = -m1.nx * LANE_OFFSET;
          m2.offsetY = -m1.ny * LANE_OFFSET;
        } else {
          // Perpendicular crossing (e.g. East vs South):
          m1.offsetX = m1.nx * LANE_OFFSET;
          m1.offsetY = m1.ny * LANE_OFFSET;
          m2.offsetX = m2.nx * LANE_OFFSET;
          m2.offsetY = m2.ny * LANE_OFFSET;
          // Ensure they don't collide if normals overlap
          const dist = Math.hypot(m1.offsetX - m2.offsetX, m1.offsetY - m2.offsetY);
          if (dist < 112) {
            m2.offsetX = -m1.nx * LANE_OFFSET;
            m2.offsetY = -m1.ny * LANE_OFFSET;
          }
        }
      } else {
        // Multiple stationary / loading movers
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

        // Check if swapping adjacent tiles between t and t+1
        if (s1.logicalX === next2.logicalX && s1.logicalY === next2.logicalY &&
            next1.logicalX === s2.logicalX && next1.logicalY === s2.logicalY) {
          const dx = next1.logicalX - s1.logicalX;
          const dy = next1.logicalY - s1.logicalY;
          const norm = getRightHandNormal(dx, dy);

          // Both movers shift into their opposing lateral passing lanes
          s1.offsetX = norm.nx * LANE_OFFSET;
          s1.offsetY = norm.ny * LANE_OFFSET;
          next1.offsetX = norm.nx * LANE_OFFSET;
          next1.offsetY = norm.ny * LANE_OFFSET;

          s2.offsetX = -norm.nx * LANE_OFFSET;
          s2.offsetY = -norm.ny * LANE_OFFSET;
          next2.offsetX = -norm.nx * LANE_OFFSET;
          next2.offsetY = -norm.ny * LANE_OFFSET;
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
