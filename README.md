# Planar System Simulator: Two-Stage Scheduling and Routing

A high-performance optimization and simulation platform for **planar magnetic levitation transport systems** (such as Beckhoff XPlanar) applied to high-throughput pharmaceutical and chemical dispensing pipelines.

This repository accompanies the research paper demonstration, providing an end-to-end environment for **Constraint Programming (CP) makespan scheduling**, **MIP-based conflict-free multi-mover routing**, **interactive 2D digital twin visualization**, and **automated experiment benchmarks**.

---

## System Overview

Planar magnetic levitation systems deploy autonomous electromagnetic movers across a modular grid of stator tiles. While offering high agility and dynamic station routing, simultaneous operation creates significant physical congestion and collision hazards.

This platform solves the coupled problem via a decoupled, two-stage architecture:

1. **Stage 1 — Task Scheduling (CPLEX CP Optimizer):** Formulates order processing as a cumulative scheduling problem with alternative sequence resources, minimizing scheduled makespan ($C_{\text{max}}^{\text{sched}}$).
2. **Stage 2 — Conflict-Free Routing:** Takes scheduled station visits and routes movers along grid tiles using a time-indexed ScheduleExtender, resolving kinetic and geometric collisions into the real routed makespan ($C_{\text{max}}^{\text{routed}}$).
3. **Overhead & Workload Instrumentation:** Quantifies routing delay ($\Delta C_{\text{max}} = C_{\text{max}}^{\text{routed}} - C_{\text{max}}^{\text{sched}}$), interruption progression, solver search trees, and dispensing-to-travel ratio ($R_{D/T}$).

---

## Benchmark Topologies
All topologies utilize 64 modular tiles arranged in distinct spatial layouts to evaluate structural congestion under identical total tile areas:

* **`square64` ($8 \times 8$ Grid):** Open planar field; maximum degrees of freedom for bypass routing.
* **`doubleline64` ($2 \times 32$ Corridor):** Narrow bidirectional corridor; creates frequent counterflow bottlenecks.
* **`line64` ($64 \times 1$ Pipeline):** Single-tile width pipeline; strict FIFO constraint with zero passing lanes.
* **`ring64` ($17 \times 17$ Hollow Loop):** Cyclic track topology; tests directional loop routing and perimeter accumulation.

Layout files are located in `data/layouts/` and `backend/data/layouts/`.

---

## Quickstart & Docker Deployment

### Prerequisites
* **Docker & Docker Compose** (v2.20+)
* **Gurobi License:** Place `gurobi.lic` in the repository root.
* **IBM CPLEX Installer:** (For Linux/AMD64 deployments) place `cplex_studio2211.linux_x86_64.bin` in the repository root.

### 1. Configure Environment
```bash
cp .env.example .env
# Ensure ports and database credentials in .env suit your environment
```

### 2. Install CPLEX into Docker Volume (One-time step on Linux/Server)
```bash
make install-cplex
# Or: docker compose --profile setup run --rm cplex_installer
```

### 3. Build and Launch Stack
```bash
make up
# Or: docker compose up -d
```

Check running services:
```bash
make ps
```

| Service | Address | Purpose |
| :--- | :--- | :--- |
| **Frontend Web App** | `http://localhost:5173` | Experiment management, layout designer, batch runner |
| **Simulation Viewer** | `http://localhost:3000` | 2D mover playback, collision inspection, Gantt timeline |
| **Backend Swagger API** | `http://localhost:8000/docs` | Interactive OpenAPI documentation and REST endpoints |

---

## Running Experiments

We provide dedicated automation scripts in `backend/scripts/` to execute all experimental matrices and export sanitized CSV datasets.

```bash
# 1. Smoke Test (~10 seconds)
docker compose exec backend python scripts/run_experiments.py --mode quick-test

# 2. Phase 3.1: Router Overhead & Congestion Matrix
# Tests mover scaling [1, 4, 8, 12] across speeds [10, 1] and topologies
docker compose exec backend python scripts/run_experiments.py --mode overhead --topology all --time-limit 600

# 3. Phase 2.1: CP Time-Limit & Scalability Study
# Tests order scaling [10, 25, 50, 99] x 8 movers x 5 seeds
docker compose exec backend python scripts/run_experiments.py --mode scalability

# 4. Phase 2.2: Lower Bound Grid
# Solves orders [25, 50, 99] x movers [2, 6, 10, 12] with long time-limits
docker compose exec backend python scripts/run_experiments.py --mode lowerbound

# 5. Phase 4.1: DAG-Based Order Batching
# Tests 99 orders x batch sizes [None, 25, 50] x 8 movers
docker compose exec backend python scripts/run_experiments.py --mode batching
```

### Exported Metrics Reference

| Column Category | Fields | Description |
| :--- | :--- | :--- |
| **Ident & Config** | `id`, `name`, `status`, `solver_name`, `seed`, `order_count` | Run identifiers and parameters |
| **Hardware / Layout** | `topology`, `mover_count`, `mover_speed` | Spatial layout and fleet capacity |
| **Makespan & Overhead** | `scheduled_cmax`, `routed_cmax`, `routing_overhead_abs`, `routing_overhead_pct` | Discrepancy between CP schedule and routed execution |
| **Runtime Breakdown** | `scheduling_time_s`, `routing_time_s`, `total_time_s` | Execution duration for CP and MIP stages |
| **Search Progress** | `routing_iterations`, `initial_interruptions`, `final_interruptions` | Conflict resolution iterations |
| **CP Bound Quality** | `cp_solve_status`, `best_bound_internal`, `internal_gap_pct`, `solver_branches`, `solver_fails` | Optimality status and relaxation bound |
| **Workload Profile** | `total_transit_time`, `total_dispensing_time`, `total_wait_time`, `dispensing_to_travel_ratio` | $R_{D/T}$ and mover time allocation |

---

## Repository Structure

```
├── backend/                  # FastAPI & Celery backend service
│   ├── api/                  # REST controllers and DTO schemas
│   ├── core/                 # App configuration & Celery broker
│   ├── db/                   # PostgreSQL models & session lifecycle
│   ├── domain/               # Domain models (Experiment, Result, Layout)
│   ├── scripts/              # Automated experiment runners & CSV export
│   │   ├── run_experiments.py
│   │   └── export_experiment_results.py
│   ├── solvers/              # Optimization solver integrations
│   │   ├── common/           # Shared simulation & routing utilities
│   │   └── cplex_medicine/   # CPLEX CP Optimizer scheduling pipeline
│   └── tests/                # Unit and integration test suites
├── frontend/                 # React 19 + Vite web interface
├── simulator/                # Next.js 14 + Pixi.js digital twin canvas
├── data/
│   ├── layouts/              # Benchmark topologies (square, line, doubleline, ring)
│   └── orders.json           # Standard 99-order pharmaceutical benchmark dataset
├── docker-compose.yml        # Orchestration for all services
├── Makefile                  # Lifecycle commands (build, up, clean, install-cplex)
└── start_all.sh              # Local development launcher
```

---

## Testing

Run backend unit tests (covers API models, metrics calculation, and CPLEX mappers):

```bash
cd backend
source .venv/bin/activate
pytest tests/unit
```

---

## Citation & License

If you use this benchmark platform or code in your research, please cite our corresponding paper.

Licensed under the [MIT License](backend/README.md).
