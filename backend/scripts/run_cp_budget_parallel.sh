#!/usr/bin/env bash
# Runs the jobs of a cp_budget_jobs.py job list in parallel Docker containers on the experiment server.
# Each container gets 1 CPU and a RAM limit, uses the code of this checkout (scripts, solvers, core mounted),
# and writes one result JSON per job. Jobs whose result file already exists are skipped, so the script can be
# restarted. Run from the repository root:
#
#     PARALLEL=20 MEM_LIMIT=12g backend/scripts/run_cp_budget_parallel.sh backend/data/results/cp_budget/jobs.txt

set -euo pipefail

JOBS_FILE=${1:?usage: run_cp_budget_parallel.sh JOBS_FILE}
PARALLEL=${PARALLEL:-20}
MEM_LIMIT=${MEM_LIMIT:-12g}
IMAGE=${IMAGE:-planar_system_simulator-celery_worker}
CPLEX_PATH=${CPLEX_PATH:-/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer}
BACKEND=$(cd "$(dirname "$0")/.." && pwd)

mkdir -p "$BACKEND/data/results/cp_budget/logs"

run_job() {
    local args="$1"
    local output
    output=$(sed -E 's/.*--output ([^ ]+).*/\1/' <<< "$args")
    [ -f "$BACKEND/$output" ] && return 0
    local log="$BACKEND/data/results/cp_budget/logs/$(basename "$output" .json).log"
    # shellcheck disable=SC2086
    docker run --rm --user "$(id -u):$(id -g)" --cpus 1 -m "$MEM_LIMIT" \
        -v "$BACKEND/scripts:/app/scripts" -v "$BACKEND/data:/app/data" \
        -v "$BACKEND/solvers:/app/solvers" -v "$BACKEND/core:/app/core" \
        -v planar_cplex_data:/opt/ibm:ro -e CPLEX_PATH="$CPLEX_PATH" -e HOME=/tmp \
        -w /app --entrypoint python "$IMAGE" scripts/run_cp_budget.py $args > "$log" 2>&1 \
        || echo "FAILED (exit $?): $args" >> "$BACKEND/data/results/cp_budget/failed.txt"
}
export -f run_job
export BACKEND MEM_LIMIT IMAGE CPLEX_PATH

xargs -P "$PARALLEL" -I {} bash -c 'run_job "$@"' _ {} < "$JOBS_FILE"
echo "All jobs processed."
