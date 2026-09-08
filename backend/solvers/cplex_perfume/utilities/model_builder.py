from docplex.cp.model import CpoModel

from solvers.cplex_perfume.models import CplexPerfumeData
from solvers.cplex_perfume.utilities.utils import proc_time, build_transition_matrix


class SchedulingModelBuilder:

    def __init__(
            self,
            recipes: list,
            ingredients: dict,
            tiles_flat: list,
            machines: dict,
            n_movers: int,
            tmax_values: list,
            data: CplexPerfumeData
    ):
        self.recipes = recipes
        self.ingredients = ingredients
        self.tiles_flat = tiles_flat
        self.machines = machines
        self.n_movers = n_movers
        self.tmax_values = tmax_values
        self.data = data

        self.mdl = CpoModel()

        # Variables & Information
        self.master = {}
        self.alt = {}
        self.var_info = {}

        # Structures facilitating constraint building
        self.tile_ops = {t.idx: [] for t in tiles_flat}
        self.mover_ops = {v: [] for v in range(n_movers)}
        self.recipe_spans_per_mover = {v: [] for v in range(n_movers)}
        self.mover_assign = {}
        self.mover_seq = {}

        # Precompute transition matrix
        self.transition = build_transition_matrix(all_tiles=tiles_flat, mover_speed=data.mover_speed)

    def _build_mover_assignments(self) -> None:
        for r in range(len(self.recipes)):
            self.mover_assign[r] = {v: self.mdl.binary_var(name=f"y_r{r}_v{v}") for v in range(self.n_movers)}
            self.mdl.add(self.mdl.sum(self.mover_assign[r][v] for v in range(self.n_movers)) == 1)

    def _build_tasks_and_alternatives(self) -> None:
        for r, ops in enumerate(self.recipes):
            self.master[r] = {}
            self.alt[r] = {}
            steps_for_mover = {v: [] for v in range(self.n_movers)}

            for op in ops:
                k = op.step

                pt = proc_time(op=op, ingredients=self.ingredients, data=self.data)

                self.alt[r][k] = []

                # The Main Master Task - represents recipe step k being done
                m_name = f"Master__{r}__{k}__{op.label.replace(' ', '_')}"
                self.master[r][k] = self.mdl.interval_var(name=m_name, length=pt)
                mover_step_intervals = []

                for v in range(self.n_movers):
                    # Intermediate level task: This mover performs this specific recipe step
                    ms_name = f"MS_r{r}_k{k}_v{v}"
                    mover_step_interval = self.mdl.interval_var(optional=True, name=ms_name, size=pt)
                    mover_step_intervals.append(mover_step_interval)
                    steps_for_mover[v].append(mover_step_interval)

                    # Link intermediate task to binary assignment
                    self.mdl.add(self.mdl.presence_of(mover_step_interval) <= self.mover_assign[r][v])

                    # 3. Leaf Tile Task
                    tile_alternatives = []
                    for tile in op.candidates:
                        v_name = f"A_r{r}_k{k}_t{tile.idx}_v{v}_{op.label.replace(' ', '_')}"
                        avar = self.mdl.interval_var(optional=True, size=pt, name=v_name)

                        tile_alternatives.append(avar)
                        self.tile_ops[tile.idx].append(avar)
                        self.mover_ops[v].append((avar, tile.idx))
                        self.alt[r][k].append(avar)

                        self.var_info[v_name] = {
                            "type": "alternative", "recipe": r, "operation": k,
                            "ingredient": op.label,
                            "mover": v, "dispenser": tile.idx,
                        }

                    # 4. Alternative Connections
                    self.mdl.add(self.mdl.alternative(mover_step_interval, tile_alternatives))
                self.mdl.add(self.mdl.alternative(self.master[r][k], mover_step_intervals))

            # Span creation
            for v in range(self.n_movers):
                r_m_span = self.mdl.interval_var(optional=True, name=f"RecipeSpan_recipe{r}_mover{v}")
                self.mdl.add(self.mdl.presence_of(r_m_span) == self.mover_assign[r][v])
                self.mdl.add(self.mdl.span(r_m_span, steps_for_mover[v]))
                self.recipe_spans_per_mover[v].append(r_m_span)

    def _build_overlap_constraints(self) -> None:
        """Prevents physical overlap on tiles and recipe interleaving on movers."""
        # Tile overlaps
        for t_idx, ops_on_tile in self.tile_ops.items():
            if len(ops_on_tile) > 1:
                self.mdl.add(self.mdl.no_overlap(ops_on_tile))

        # Reservoir constraints
        for v in range(self.n_movers):
            if self.recipe_spans_per_mover[v]:
                self.mdl.add(self.mdl.no_overlap(self.recipe_spans_per_mover[v]))

    def _build_precedence_constraints(self) -> None:
        """Enforces phase ordering within recipes."""
        PHASE_ORDER = [0, 1, 2, 3, 4, 5, 6, 7]
        for r, ops in enumerate(self.recipes):
            by_phase = {}
            for op in ops:
                by_phase.setdefault(op.phase, []).append(self.master[r][op.step])

            present_phases = [p for p in PHASE_ORDER if p in by_phase]
            for i in range(len(present_phases) - 1):
                p_cur, p_next = present_phases[i], present_phases[i + 1]
                max_end = self.mdl.max([self.mdl.end_of(iv) for iv in by_phase[p_cur]])
                min_start = self.mdl.min([self.mdl.start_of(iv) for iv in by_phase[p_next]])

                self.mdl.add(max_end <= min_start)

    def _build_routing_constraints(self) -> None:
        """ Distance-aware setup times"""
        for v in range(self.n_movers):
            if self.mover_ops[v]:
                intervals = [item[0] for item in self.mover_ops[v]]
                types = [item[1] for item in self.mover_ops[v]]

                self.mover_seq[v] = self.mdl.sequence_var(vars=intervals, types=types, name=f"SEQ_v{v}")
                self.mdl.add(self.mdl.no_overlap(self.mover_seq[v], self.transition))

    def _enforce_tmax(self) -> None:
        """Enforces T_max for each recipe."""
        for r, ops in enumerate(self.recipes):
            top_step = next((op.step for op in ops if op.phase == 2), None)
            capper_step = next((op.step for op in ops if op.phase == 7), None)
            if top_step is not None and capper_step is not None:
                self.mdl.add(
                    self.mdl.end_of(self.master[r][capper_step]) -
                    self.mdl.start_of(self.master[r][top_step])
                    <= self.tmax_values[r]
                )

    def set_objective(self) -> None:
        """Minimize makespan """
        last_op_per_recipe = [
            self.master[r][len(ops) - 1] for r, ops in enumerate(self.recipes)
        ]
        makespan = self.mdl.integer_var(name="makespan")
        self.mdl.add(makespan == self.mdl.max(self.mdl.end_of(iv) for iv in last_op_per_recipe))
        self.mdl.minimize(makespan)

    def build(self) -> dict:
        self._build_mover_assignments()
        self._build_tasks_and_alternatives()
        self._build_overlap_constraints()
        self._build_precedence_constraints()
        self._build_routing_constraints()
        self._enforce_tmax()
        self.set_objective()

        return {
            "model": self.mdl,
            "master": self.master,
            "mover_assign": self.mover_assign,
            "mover_seq": self.mover_seq,
            "alt": self.alt,
            "var_info": self.var_info,
        }
