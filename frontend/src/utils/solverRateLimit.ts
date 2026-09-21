const RATE_LIMIT_KEY = 'solver_last_run_timestamp';
const COOLDOWN_MS = 60 * 60 * 1000; // 1 hour in milliseconds

export interface RateLimitStatus {
    allowed: boolean;
    remainingMs: number;
}

/**
 * Checks whether the solver can be used right now.
 * Returns whether it's allowed and the remaining cooldown in ms.
 */
export function checkSolverRateLimit(): RateLimitStatus {
    const lastRun = localStorage.getItem(RATE_LIMIT_KEY);
    if (!lastRun) {
        return {allowed: true, remainingMs: 0};
    }

    const elapsed = Date.now() - Number(lastRun);
    if (elapsed >= COOLDOWN_MS) {
        return {allowed: true, remainingMs: 0};
    }

    return {allowed: false, remainingMs: COOLDOWN_MS - elapsed};
}

/**
 * Records that the solver was just used (stamps current time).
 */
export function recordSolverUsage(): void {
    localStorage.setItem(RATE_LIMIT_KEY, String(Date.now()));
}

/**
 * Formats remaining milliseconds into a human-readable string like "42 min 15 sec".
 */
export function formatRemainingTime(ms: number): string {
    const totalSeconds = Math.ceil(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (minutes === 0) return `${seconds}s`;
    if (seconds === 0) return `${minutes}m`;
    return `${minutes}m ${seconds}s`;
}
