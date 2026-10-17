#!/usr/bin/env bash
# Runs the jobs of a cp_budget_jobs.py job list in parallel Docker containers on the experiment server.
# Each container gets 1 CPU and a RAM limit, uses the code of this checkout (scripts, solvers, core mounted),
# and writes one result JSON per job. Jobs whose result file already exists are skipped, so the script can be
# restarted. Run from the repository root:
#
#     PARALLEL=20 MEM_LIMIT=12g backend/scripts/run_cp_budget_parallel.sh backend/data/results/cp_budget/jobs.txt
#
# Logs and failures go to the folder of the job list. The Gurobi license of the repository root is mounted for
# warm-start jobs, together with a gurobi.env that limits Gurobi to one thread (without it, Gurobi starts 32
# threads in the 1-CPU container and the warm start is about 25 times slower). Run the warm-start cache jobs
# (--warm-only) with PARALLEL=2 at most.

set -euo pipefail

JOBS_FILE=${1:?usage: run_cp_budget_parallel.sh JOBS_FILE}
PARALLEL=${PARALLEL:-20}
MEM_LIMIT=${MEM_LIMIT:-12g}
IMAGE=${IMAGE:-planar_system_simulator-celery_worker}
CPLEX_PATH=${CPLEX_PATH:-/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer}
BACKEND=$(cd "$(dirname "$0")/.." && pwd)
RUN_DIR=$(cd "$(dirname "$JOBS_FILE")" && pwd)

mkdir -p "$RUN_DIR/logs"
printf "Threads 1\n" > "$RUN_DIR/gurobi.env"

run_job() {
    local args="$1"
    local output
    if [[ "$args" == *"--output "* ]]; then
        output=$(sed -E 's/.*--output ([^ ]+).*/\1/' <<< "$args")
        [ -f "$BACKEND/$output" ] && return 0
    else
        output=$(sed -E 's/.*--warm-cache ([^ ]+).*/\1/' <<< "$args")
    fi
    local log="$RUN_DIR/logs/$(basename "$output" .json).log"
    # shellcheck disable=SC2086
    docker run --rm --user "$(id -u):$(id -g)" --cpus 1 -m "$MEM_LIMIT" \
        -v "$BACKEND/scripts:/app/scripts" -v "$BACKEND/data:/app/data" \
        -v "$BACKEND/solvers:/app/solvers" -v "$BACKEND/core:/app/core" \
        -v planar_cplex_data:/opt/ibm:ro -e CPLEX_PATH="$CPLEX_PATH" -e HOME=/tmp \
        -v "$BACKEND/../gurobi.lic:/opt/gurobi/gurobi.lic:ro" -e GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic \
        -v "$RUN_DIR/gurobi.env:/app/gurobi.env:ro" \
        -w /app --entrypoint python "$IMAGE" scripts/run_cp_budget.py $args > "$log" 2>&1 \
        || echo "FAILED (exit $?): $args" >> "$RUN_DIR/failed.txt"
}
export -f run_job
export BACKEND RUN_DIR MEM_LIMIT IMAGE CPLEX_PATH

xargs -P "$PARALLEL" -I {} bash -c 'run_job "$@"' _ {} < "$JOBS_FILE"
echo "All jobs processed."
