/**
 * Trajectory Post-Processor for Multi-Mover Grid Simulation
 *
 * Implements:
 * 1. Centered grid travel: All movers travel straight through the tile center.
 * 2. Multi-mover stack detection: When multiple movers occupy the same tile,
 *    applies a subtle stack offset (8px) so all movers remain visible like stacked cards.
 * 3. Rest site offsets: Preserves wait_rest offsets.
 */

export const CELL_SIZE = 240;
export const MOVER_SIZE = 112;

/**
 * Processes raw simulation paths into exact pixel coordinates.
 *
 * @param {Array<Array<Object>>} allPaths - Array of mover paths from simulationData
 * @returns {Array<Array<Object>>} Processed paths with calculated x, y, logicalX, logicalY, stackCount, stackIdx
 */
export function processMoverTrajectories(allPaths) {
  if (!allPaths || allPaths.length === 0) return [];

  const numMovers = allPaths.length;
  const numSteps = allPaths[0].length;
  const baseCenterOffset = (CELL_SIZE - MOVER_SIZE) / 2;

  // Step 1: Base positions (all centered on tile)
  const processed = allPaths.map((path, moverIdx) => {
    return path.map((step, t) => {
      const logicalX = step.x;
      const logicalY = step.y;
      const mode = step.mode;

      let offsetX = 0;
      let offsetY = 0;

      if (mode === 'wait_rest') {
        offsetX = (step.rest_offset_x || 0) * (CELL_SIZE / 2);
        offsetY = (step.rest_offset_y || 0) * (CELL_SIZE / 2);
      }

      return {
        ...step,
        logicalX,
        logicalY,
        baseX: logicalX * CELL_SIZE + baseCenterOffset,
        baseY: logicalY * CELL_SIZE + baseCenterOffset,
        offsetX,
        offsetY,
        stackCount: 1,
        stackIdx: 0,
        moverIdx,
      };
    });
  });

  // Step 2: Detect tiles with multiple occupants to apply subtle stack offset and count
  for (let t = 0; t < numSteps; t++) {
    const tileOccupants = new Map();

    for (let m = 0; m < numMovers; m++) {
      const step = processed[m][t];
      // Skip wait_rest if it already has a dedicated offset
      if (step.mode === 'wait_rest' && (step.offsetX !== 0 || step.offsetY !== 0)) continue;

      const key = `${step.logicalX},${step.logicalY}`;
      if (!tileOccupants.has(key)) {
        tileOccupants.set(key, []);
      }
      tileOccupants.get(key).push(step);
    }

    for (const [key, occupants] of tileOccupants.entries()) {
      const count = occupants.length;
      if (count > 1) {
        occupants.forEach((step, idx) => {
          step.stackCount = count;
          step.stackIdx = idx;
          // Subtle stacked card offset: 8px spread so all are visible
          const spread = 8;
          const shift = (idx - (count - 1) / 2) * spread;
          step.offsetX += shift;
          step.offsetY -= shift;
        });
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
