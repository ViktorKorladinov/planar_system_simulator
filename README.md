# Planar System Simulator

Scheduling, routing and simulation for planar magnetic transport systems (e.g. Beckhoff XPlanar), applied to
personalized drug dispensing. The repository accompanies the Tile-Glider demonstration paper and contains the
experiment backend, a web configurator for layouts and experiments, and a 2D trajectory viewer.

## How it works

The problem is solved in two stages:

1. **Scheduling** (IBM CPLEX CP Optimizer). Orders are split into dispensing tasks, which are assigned to movers
   and dispensers and sequenced to minimize the makespan of the schedule (`scheduled_cmax`).
2. **Routing** (Gurobi). The scheduled station visits are turned into tile-by-tile mover paths. Conflicts on
   tiles are resolved by delaying tasks and re-optimizing start times, which gives the routed makespan
   (`routed_cmax`).

The difference between the two makespans is reported as the routing overhead, together with interruption
counts, solver statistics and the dispensing-to-travel ratio R_D/T.

## Benchmark layouts

All layouts have 64 tiles:

- `square64`: 8 × 8 grid.
- `doubleline64`: 2 × 32 corridor.
- `line64`: single row of 64 tiles, no passing.
- `ring64`: hollow 17 × 17 loop.

Layout files are in `data/layouts/` and `backend/data/layouts/`.

## Running with Docker

Requirements: Docker Compose v2.20+, a Gurobi license (`gurobi.lic` in the repository root) and, on Linux/AMD64,
the CPLEX installer `cplex_studio2211.linux_x86_64.bin` in the repository root.

```bash
cp .env.example .env      # adjust ports and database credentials if needed
make install-cplex        # one-time: installs CPLEX into a Docker volume
make up                   # starts the stack
make ps                   # lists running services
```

| Service | Address |
| :--- | :--- |
| Configurator (layouts, experiments, batch runner) | `http://localhost:5173` |
| Simulation viewer (playback, Gantt timeline) | `http://localhost:3000` |
| Backend API (Swagger) | `http://localhost:8000/docs` |

## Running experiments

`backend/scripts/run_experiments.py` creates the layouts and order lists, submits an experiment matrix and can
export the results to CSV.

```bash
# Smoke test (about 10 s)
docker compose exec backend python scripts/run_experiments.py --mode quick-test

# Routing overhead: movers [1, 4, 8, 12] x speeds [10, 1] x all topologies
docker compose exec backend python scripts/run_experiments.py --mode overhead --topology all --time-limit 600

# Scalability: orders [10, 25, 50, 99] x 8 movers x 5 seeds
docker compose exec backend python scripts/run_experiments.py --mode scalability

# Lower bounds: orders [25, 50, 99] x movers [2, 6, 10, 12]
docker compose exec backend python scripts/run_experiments.py --mode lowerbound

# Batching: 99 orders x batch sizes [None, 25, 50] x 8 movers
docker compose exec backend python scripts/run_experiments.py --mode batching
```

### Exported columns

| Group | Fields |
| :--- | :--- |
| Run and configuration | `id`, `name`, `status`, `solver_name`, `seed`, `order_count` |
| Layout and fleet | `topology`, `mover_count`, `mover_speed` |
| Makespan | `scheduled_cmax`, `routed_cmax`, `routing_overhead_abs`, `routing_overhead_pct` |
| Runtime | `scheduling_time_s`, `routing_time_s`, `total_time_s` |
| Routing iterations | `routing_iterations`, `initial_interruptions`, `final_interruptions` |
| CP solver | `cp_solve_status`, `best_bound_internal`, `internal_gap_pct`, `solver_branches`, `solver_fails` |
| Mover time | `total_transit_time`, `total_dispensing_time`, `total_wait_time`, `dispensing_to_travel_ratio` |

## Repository structure

```
backend/          FastAPI + Celery service
  api/            REST routers and DTOs
  core/           configuration, Celery app
  db/             SQLAlchemy models, Alembic migrations
  domain/         domain models
  scripts/        experiment runner and CSV export
  solvers/        scheduling (cplex_medicine) and shared routing code (common)
  tests/          unit and integration tests
frontend/         React + Vite configurator
simulator/        Next.js trajectory viewer
data/             benchmark layouts and the 99-order dataset
docker-compose.yml
Makefile
start_all.sh      local development launcher
```

More detail on the backend internals is in `DEVELOPMENT.md`.

## Tests

```bash
cd backend
.venv/bin/python -m pytest tests/unit
```

## License

MIT, see [backend/LICENSE](backend/LICENSE).
