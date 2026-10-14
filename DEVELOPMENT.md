# micka: scheduling, routing, digital twin, experiments

`backend/` is the source of truth for scheduling, lower bounds, routing, and operational experiment results.
Paths below are relative to `backend/` unless stated otherwise.

## Architecture

- FastAPI app (`main.py`, `api/routers/`), PostgreSQL via SQLAlchemy/Alembic (`db/`, `alembic/`),
  Celery + Redis task queue (`core/celery_app.py`, `clients/tasks/celery_tasks.py`).
- `../frontend/`: React/Vite experiment configurator. `../simulator/`: Next.js trajectory viewer (digital twin).
- Run path: `POST /api/v1/experiments/batch/matrix` (or `/batch/`) →
  `services/experiment_service.py` (persists experiments, enqueues) → Celery `solve_experiment_task` →
  `run_solver` → `solvers/factory.py` → `CplexMedicineExperimentSolver.solve`
  (`solvers/cplex_medicine/experiment_solver.py`, thin wrapper) → `LargeScheduleCreator` (CP) →
  `create_simulation` (routing) → `Result` stored in the DB.
- `solvers/hexaly/` and `solvers/cplex_perfume/` exist but are not used in the paper.

## Scheduling: `solvers/cplex_medicine/`

- `utilities/batch_handler.py` (`ScheduleCreator`) holds the CP Optimizer model:
  - optional interval alternatives per (mover, dispenser), linked by `alternative`;
  - `no_overlap` per mover with a transition matrix of BFS shortest-path distances (`PathOptimizer`);
  - `no_overlap` per tile and per dispenser;
  - one optional wrapper interval per (order, mover), `no_overlap` of wrappers per mover, and presence
    linking, so a mover processes one whole order at a time ("take-give" behaviour; no cumul/reservoir functions);
  - objective: minimize max end time.
- Durations: drug quantity × `dispensing_time`. Interface operations are hard-coded to 3 ticks
  (`handle_input`); `configuration.interface_time` is ignored.
- Batching: `run_multiple_batches` cuts the order list into consecutive slices of `batch_size`;
  `merge_schedules` concatenates them with a fixed offset of `rows + cols`. There is no explicit DAG merge; the
  routing compression step later re-optimizes start times globally.
- `utilities/large_schedules_handler.py`: sets the CP Optimizer path (`CPLEX_PATH`, or `ARM64_PATH` on arm),
  runs batches, aggregates solver metrics.
- `utilities/lowerbound_heuristic.py`: per-order GTSP (Noon–Bean) solved as a TSP with Gurobi lazy subtour cuts,
  then P||Cmax MIP in Gurobi (20 s limit). The incumbent becomes `warm_start_cmax`; its mover–order assignment
  warm-starts the CP model when `warmup=True`.
- `models.py`, `mapper.py`: pydantic models and domain → CP input mapping.

## Routing: `solvers/common/utilities/`

- `simulation_creator.py` (`create_simulation`) orchestrates routing:
  1. `scheduled_cmax` = CP makespan (taken before compression);
  2. `ScheduleExtender.optimize(compress=True)`;
  3. loop: build paths → count interruptions → extend durations → re-solve, until no task needs more ticks
     than already added (`TicksAdded`);
  4. `routed_cmax` = longest mover path; also computes R_D/T and other metrics.
- `schedule_extender.py`: Gurobi LP minimizing makespan over fixed precedences: consecutive tasks of a mover
  (+ travel time) and consecutive tasks on the same physical tile.
- `interruptions_counter.py`: per task, counts time steps in which another mover transits its tile while it
  dispenses, plus transit-capacity penalties: when more than 3 movers transit one tile at a tick, the excess
  movers (highest ids) get delays 1, 2, … on their last finished task, once per continuous event.
- `multimed_path_maker_car.py`: builds step-by-step mover paths (`MoverStep`, modes loading / transit /
  wait_rest / e), including detours to resting sites.
- `path_optimizer.py`: BFS shortest paths on the layout graph (respects blocked tiles and ring/line shape),
  plus a least-used variant among all shortest paths.
- `routing_sites.py`: resting-site generation ILP (≤1 site per tile, ≤2 at interfaces).
  `resting_site_optimizer.py`: assigns idle periods to resting sites (ILP over a conflict graph).
- `schedule_visualiser.py`: Gantt charts. `convs.py`: string ↔ coordinate/mover helpers.

## Data

- `data/orders.json`: 99 orders (3–7 drugs, 34 distinct drugs). No larger order sets exist in micka.
- `data/layouts/{square,doubleline,line,ring}64.json`: 64-tile benchmarks, 80 dispensers each;
  60 dispenser tiles + 4 interfaces (doubleline: 62 + 2). Identical copies exist in `../data/layouts/`,
  `../orders.json`, and `data/square64.json`.
- Experiment order sets: `scripts/run_experiments.py` creates `Orders_Full_Seed1..5` as shuffles of the same
  99 orders, and `Orders_N{n}_Seed{s}` as random subsets.
- Do not change benchmark data without asking.

## Scripts: `scripts/`

- `run_experiments.py`: REST client that creates layouts/order lists and submits a matrix.
  Modes: quick-test, overhead, scalability, batching, lowerbound. Default `--time-limit 600`; the paper
  runs used `--time-limit 300`.
- `export_experiment_results.py`: exports finished experiments of a batch to CSV via the API.
- `audit_routing_paths.py`: post-hoc check of final mover paths (transit capacity, same-tile dispensing).
- `summarize_overhead_matrix.py`: builds the routing tables (`routing_cmax_effect_*.tex`,
  `warmup_comparison.tex`) and in-text numbers from the overhead CSV, with reruns replacing originals.
- Result CSVs of the paper batches: `data/plots/*_results.csv`. Other paper figures (time limit, batch size,
  robustness, mover-count plots, LB table) read CSVs in `../../xplanar/experiments/`, not from micka scripts.

## Environment

- Requires CPLEX CP Optimizer 22.1.1 and a Gurobi license (`gurobi.lic` in repo root; gitignored).
- Local tests (Python 3.10 venv in `backend/.venv`; use `python -m pytest`, the `pytest` shim has a stale path):
  `cd backend && .venv/bin/python -m pytest tests/unit`. Integration tests need Postgres from
  `backend/docker-compose.yml`.
- Full stack: `cp .env.example .env`, `make install-cplex`, `make up`, then
  `docker compose exec backend python scripts/run_experiments.py --mode quick-test` (10 orders, 2 movers, 10 s).
- Local dev without Docker for the app: `start_all.sh`. `core/config.py` `ARM64_PATH` is hard-coded to a local
  CPLEX_Studio2212 install.

## Experiment server: `ssh vortex-ext`

- Host `vortex` (2× AMD EPYC 9124, 377 GiB, NixOS); repo at `~/planar_system_simulator`, run with
  `docker compose` (containers: Debian 13, Python 3.10, Gurobi 13.0.3, CPLEX 22.1.1).
- Only `backend/scripts` and `backend/data` are mounted into the containers. Solver code is baked into the
  image: after changing solver code, `git pull` on the server, then
  `docker compose build backend celery_worker && docker compose up -d backend celery_worker`.
  Verify with md5/grep inside `planar_celery_worker`.
- The Celery worker runs with `-P solo` and experiments use `process_amount=1`: one run at a time, one CP
  worker. A 300 s run takes about 6.5 min including routing.
- `/app/data/plots` is a named Docker volume, not the host folder. Inside the container pass
  `--api-url http://localhost:8000` (the env `BACKEND_URL` points to the public URL). Listing 100 experiments
  can take more than 30 s.
- The public deployment (`xplan-sim` / `xplan-cfg.iid.ciirc.cvut.cz`) is served from the same stack;
  restarting backend/worker interrupts it.
- Paper batches in the DB: 4 = overhead matrix (320), 5 = scalability, 6 = batching, 7 = lower bound,
  10/11 = reruns of overhead runs affected by the routing fixes (names `Rerun of … (exp <id>)`).

## Known issues (not fixed)

- Lower bound: `orig_distances = len(path)` is distance + 1, and the 20 s Gurobi incumbent is used as a
  bound; in batch 7, 42/240 runs have LB > CP makespan.
- `scheduled_cmax` is measured before compression, so batched runs can show negative routing overhead.
- R_D/T counts all loading steps, including interface operations and the initial wait before a mover's
  first task.
- `ScheduleCreator.__init__` builds `self.movers` from `dispensing_time` (only affects the visualizer).
- Batches 4–7 ran before the tile-lock and transit-capacity fixes (image built 2026-09-21).

## Rules

- Ask before running full experiment batches; verify on a small instance first.
- If a code change can affect reported results, say so; paper tables must be regenerated
  (`summarize_overhead_matrix.py`).
