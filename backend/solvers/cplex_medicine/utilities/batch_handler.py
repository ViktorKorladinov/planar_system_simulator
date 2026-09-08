from collections import OrderedDict

import numpy as np
import pandas as pd
from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoSequenceVarSolution

from domain.enums import LayoutType
from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.common.utilities.schedule_visualiser import ScheduleVisualizer
from solvers.cplex_medicine.models import BatchResult
from solvers.cplex_medicine.models import CplexExperimentModel
from solvers.cplex_medicine.utilities.lowerbound_heuristic import get_patient_arrangement

pd.options.mode.chained_assignment = None
np.float_ = np.float64


class ScheduleCreator:
    def __init__(self, data) -> None:
        self.data = data

        # Load data
        self.drug_names = []
        self.patients_df = None
        self.handle_input(data)

        # Generate layout
        self.machine_pos = []
        self.rows = 0
        self.cols = 0
        self.unavailable_coords = None
        self.gen_positions()
        self.filled = self.data.layout.type == LayoutType.SQUARE or self.data.layout.type == LayoutType.CUSTOM

        # Process layout
        self.coord_dict, self.start_points = self.gen_coord_dict()
        self.distance_matrix = self.calculate_distance_matrix()

        # Initialize movers
        self.movers = [f'mover{x}' for x in range(data.dispensing_time)]

        # Visualization
        self.visualizer = None
        self.initialize_visualizer()

    def handle_input(self, data: CplexExperimentModel) -> None:
        """Initializes patients variable with all patients from experiment.

        Args:
            data: Experiment data.
        """
        self.drug_names = []

        for names_row in self.data.layout.placement:
            self.drug_names += names_row

        selected_patients = data.orders
        patients_df = pd.DataFrame([p.model_dump() for p in selected_patients])
        patients_df['drug_names'] = patients_df['drug_names'].apply(lambda x: ['interface', 'interface'] + x)
        patients_df['dosages'] = patients_df['dosages'].apply(
            lambda x: [3, 3] + [i * self.data.dispensing_time for i in x])
        self.patients_df = patients_df

    def gen_positions(self) -> None:
        """
        Initializes class variables universally based on the 2D placement grid.
        """
        self.rows, self.cols = self.data.layout.row_amount, self.data.layout.column_amount
        unavailable_coords = []

        for j, row in enumerate(self.data.layout.placement):
            for i, element in enumerate(row):
                if element == 'blocked':
                    unavailable_coords.append([i, j])

        self.machine_pos = [[i, j] for j in range(self.rows) for i in range(self.cols)]
        self.unavailable_coords = unavailable_coords

    def gen_coord_dict(self):
        """Create a dictionary mapping each medicine to its dispensers' locations"""
        coordinate_dict = OrderedDict()
        # Go through each tile
        for i, tile in enumerate(self.drug_names):
            if tile in ['empty', 'blocked']:
                continue
            meds = tile.split(',')
            # For each dispenser on the given tile, add this coord to the correct entry value
            for med in meds:
                if med not in coordinate_dict:
                    coordinate_dict[med] = []
                coordinate_dict[med].append(self.machine_pos[i])

        # Save how many dispensers are for each drug
        start_points = {}
        cumul = 0
        for name, arr in coordinate_dict.items():
            l = len(arr)
            start_points[name] = {'start': cumul, 'length': l}
            cumul += l
        return coordinate_dict, start_points

    def calculate_distance_matrix(self):
        """
            Calculate the distance between every two dispensers
        """
        num_dispensers = sum(len(coords) for coords in self.coord_dict.values())
        matrix = np.zeros((num_dispensers, num_dispensers), dtype=int)
        path_optimizer = PathOptimizer(self.rows, self.cols, self.filled, self.unavailable_coords)

        # Calculate distance between every two drugs
        for medicine_name, coords in self.coord_dict.items():
            for i in range(len(coords)):
                for other_medicine_name, other_coords in self.coord_dict.items():
                    for j, other_coord in enumerate(other_coords):
                        path = path_optimizer.find_shortest_path((coords[i][0], coords[i][1]),
                                                                 (other_coord[0], other_coord[1]))
                        distance = len(path) - 1
                        x = self.start_points[medicine_name]['start'] + i
                        y = self.start_points[other_medicine_name]['start'] + j
                        matrix[x, y] = distance

        return matrix

    def initialize_visualizer(self):
        """
            Initialize visualization tools
        """
        self.visualizer = ScheduleVisualizer(self.movers, self.coord_dict)

    def create_tasks(self, patients_df):
        """
            Create a list of objects representing drug loading tasks
        """
        tasks = []

        def add_var(patient):
            for name, dose in zip(patient['drug_names'], patient['dosages']):
                tasks.append({"patient": patient.name, "name": name, "duration": dose})

        patients_df.apply(add_var, axis=1)
        return tasks

    def gen_ranges(self, patients_df, tasks):
        """
            Generate ranges for movers, tasks, patients, and interfaces
        """
        movers = [f'mover{x}' for x in range(self.data.mover_amount)]
        movers_len, m_range = len(movers), range(len(movers))
        tasks_len, t_range = len(tasks), range(len(tasks))
        patients_len, p_range = len(patients_df), range(len(patients_df))
        interfaces_len = self.data.layout.interface_amount
        i_range = range(interfaces_len)

        return (
            movers,
            (movers_len, tasks_len, patients_len, interfaces_len),
            (m_range, t_range, p_range, i_range)
        )

    def gen_task_vars(self, patients_df, tasks, model):
        """
            Create CPLEX interval variables for tasks
        """
        task_vars = []
        tasks_by_patients = {x: [] for x in patients_df.index}
        for patient_id, item in enumerate(tasks):
            var = model.interval_var(length=item['duration'], name=item['name'])
            tasks_by_patients[item['patient']].append(patient_id)
            task_vars.append(var)
        return task_vars, tasks_by_patients

    def gen_seq_vars(self, model, ranges, movers, tasks, task_vars):
        """
            Generate sequence variables for tasks
        """
        m_range, t_range, p_range, i_range = ranges
        alt_task = []
        metadata_vis = {}
        tasks_by_meds = {name: [[] for _ in arr] for name, arr in self.coord_dict.items()}
        tasks_by_tiles = dict()
        alt_tasks_start_point = []
        interfaces = [[[[] for _ in i_range] for _ in p_range] for _ in m_range]

        # For each mover
        for i, m in enumerate(movers):
            temp = []
            # For each task
            for t in t_range:
                if i == 0:
                    alt_tasks_start_point.append(len(temp))
                medicine, patient = tasks[t]["name"], tasks[t]["patient"]
                # For each tile where this medicine is being dispensed
                for disp_id, place in enumerate(self.coord_dict[medicine]):
                    # NAME_OF_MEDICINE#MOVER_NAME#pPATIENT_ID#dDISPENSER_ID
                    name = f'{medicine}#{m}#p{patient}#d{disp_id}'
                    var = model.interval_var(optional=True, name=name, length=task_vars[t].get_length())
                    metadata_vis[name] = {
                        'patient': patient,
                        'medicine': medicine,
                        'disp_id': disp_id,
                        'mover': m
                    }
                    tile = f"{place[0]}x{place[1]}"
                    if tile in tasks_by_tiles:
                        tasks_by_tiles[tile].append(var)
                    else:
                        tasks_by_tiles[tile] = [var]
                    if medicine == 'interface':
                        interfaces[i][patient][disp_id].append(var)
                    temp.append(var)
                    tasks_by_meds[medicine][disp_id].append(var)
            alt_task.append(temp)

        return (alt_task, metadata_vis, tasks_by_meds, alt_tasks_start_point,
                interfaces, tasks_by_tiles)

    def gen_setup_time(self, alt_task, metadata_vis):
        """
            Generate setup time matrix
        """
        sequence = alt_task[0]
        seq_len = len(sequence)
        setup_time = np.zeros((seq_len, seq_len), dtype=int)
        for i in range(seq_len):
            for j in range(seq_len):
                patient, medicine, disp_id, mover = metadata_vis[sequence[i].get_name()].values()
                other_patient, other_medicine, other_disp_id, other_mover = metadata_vis[
                    sequence[j].get_name()].values()
                position_of_medicine = self.start_points[medicine]['start'] + disp_id
                position_of_other_medicine = self.start_points[other_medicine]['start'] + other_disp_id
                setup_time[i, j] = self.distance_matrix[position_of_medicine, position_of_other_medicine]

        return setup_time

    def gen_sequences_movers_meds(self, alt_task, m_range, tasks_by_meds, model):
        """
            Generate sequence variables for movers and meds
        """
        seq_mover_tasks = [model.sequence_var(alt_task[m], name='alt_seq') for m in m_range]
        seq_identical_meds = [
            [model.sequence_var([task for task in dispenser]) for dispenser in medicine]
            for medicine in tasks_by_meds.values()
        ]
        return seq_mover_tasks, seq_identical_meds

    def gen_wrappers(self, tasks_by_patients, m_range, metadata_vis, movers, model, tasks_by_tiles):
        """
            Generate wrapper variables for tasks
        """
        task_wrappers = []
        tile_wrappers = []

        for m in m_range:
            temp = []
            for key, task_indices in tasks_by_patients.items():
                mvar = model.interval_var(name=f'wrapForPatient{key}mover{m}', optional=True)
                metadata_vis[f'wrapForPatient{key}mover{m}'] = {'mover': movers[m], 'patient': key}
                temp.append(mvar)
            task_wrappers.append(temp)

        mover_patients_wrappers = [model.sequence_var(task_wrappers[m], name=f"wrapper") for m in m_range]

        for tile, vars in tasks_by_tiles.items():
            tile_wrappers.append(model.sequence_var(vars, name=f"tile{tile}Wrapper"))

        return task_wrappers, mover_patients_wrappers, tile_wrappers

    def add_constraints(self, model, ranges, sequence_meds, sequence_identical_meds, mover_patients_wrappers,
                        setup_time, alt_tasks_start_point, task_vars, alt_task, tasks_by_patients,
                        task_wrappers, tile_wrappers, interfaces):
        """
            Add constraints to the model
        """
        m_range, t_range, _, i_range = ranges

        # No overlap constraints for movers
        for mover in m_range:
            model.add(model.no_overlap(sequence_meds[mover], setup_time))
            model.add(model.no_overlap(mover_patients_wrappers[mover]))

        # No overlap constraints for identical medications
        for medicine in sequence_identical_meds:
            for dispenser in medicine:
                model.add(model.no_overlap(dispenser))

        # Task alternatives constraints
        for t in t_range:
            num_of_dispensers_for_task = self.start_points[task_vars[t].get_name()]['length']
            start_point = alt_tasks_start_point[t]
            # Each task can go in one mover and be filled by one dispenser
            task_alternatives = [alt_task[m][start_point + i] for m in m_range for i in
                                 range(num_of_dispensers_for_task)]
            model.add(model.alternative(task_vars[t], task_alternatives))

        # No overlap constraints for tiles
        for dispensers_on_tile_wrapper in tile_wrappers:
            model.add(model.no_overlap(dispensers_on_tile_wrapper))

        # Patient-specific constraints
        for patient_id, task_indices in tasks_by_patients.items():
            # For every mover
            for m in m_range:
                wrapper = task_wrappers[m][patient_id]
                first = True
                prev = None
                inlets = [interfaces[m][patient_id][i][0] for i in i_range]
                outlets = [interfaces[m][patient_id][i][1] for i in i_range]
                # If one task is on the mover, all tasks for this patient are on it. If not, none are.
                for t in task_indices:
                    num_of_dispensers_for_task = self.start_points[task_vars[t].get_name()]['length']
                    curr_start_point = alt_tasks_start_point[t]
                    task_all_disp = [alt_task[m][curr_start_point + i] for i in range(num_of_dispensers_for_task)]
                    curr_task_sum = model.sum([model.presence_of(task) for task in task_all_disp])
                    model.add([model.start_before_start(inlet, task) for task in task_all_disp for inlet in inlets])
                    model.add([model.end_before_end(task, outlet) for task in task_all_disp for outlet in outlets])
                    if first:
                        first = False
                        prev = curr_task_sum
                        # Wrapper present for this mover only if patient is being executed on this mover
                        model.add(curr_task_sum == model.presence_of(wrapper))
                        model.add([model.start_at_start(wrapper, inlet) for inlet in inlets])
                        model.add([model.end_at_end(outlet, wrapper) for outlet in outlets])
                    else:
                        model.add(curr_task_sum == prev)

    def solve(self, model, task_vars, t_range):
        """
            Solve the model and return the solution variables
        """
        obj = model.max([model.end_of(task_vars[i]) for i in t_range])
        model.minimize(obj)
        result = model.solve(TimeLimit=self.data.time_limit, LogVerbosity='Terse', Workers=self.data.process_amount)
        solution = result.get_solution()
        variables = solution.get_all_var_solutions()
        return variables

    def parse_solution(self, variables, metadata_vis):
        """
            Parse the solution variables into dataframes
        """
        intervals_arr = []
        wrappers = []

        for var in variables:
            if isinstance(var, CpoSequenceVarSolution):
                if var.get_name() and var.get_name().startswith("tile"):
                    intervals_arr.append((var.get_interval_variables(), var.get_name()[:-7]))
                elif var.get_name() and var.get_name().startswith("wrapper"):
                    wrappers.append(var.get_interval_variables())

        tasks_sol = []
        # For each mover
        for intervals, tile in intervals_arr:
            # For each task on that mover
            for (patient_id, interval) in enumerate(intervals):
                tasks_sol.append(
                    dict(Task=f"Job {patient_id + 1}", Medicine=metadata_vis[interval.get_name()]['medicine'],
                         Tile=tile, Patient=metadata_vis[interval.get_name()]['patient'],
                         Length=interval.get_length(), Start=interval.get_start(),
                         Mover=metadata_vis[interval.get_name()]['mover'],
                         Finish=interval.get_end(), Dispenser=metadata_vis[interval.get_name()]['disp_id']))

        results = pd.DataFrame(tasks_sol)

        wrappers_sol = []
        i = 0
        for mover in wrappers:
            for patient in mover:
                wrappers_sol.append(dict(Task=f"wrapper{i}", Length=patient.get_length(),
                                         Start=patient.get_start(), Mover=metadata_vis[patient.get_name()]['mover'],
                                         Patient=metadata_vis[patient.get_name()]['patient'],
                                         Finish=patient.get_end()))
                i += 1

        wrapper_results = pd.DataFrame(wrappers_sol)
        return results, wrapper_results

    def apply_warmup(self, m, task_wraps, m_range, p_range, path_optimizer: PathOptimizer):
        """
            Apply warmup solution if requested
        """
        warm_cmax = None
        if self.data.warmup:
            g_model, warm_df, warm_x = get_patient_arrangement(
                path_optimizer=PathOptimizer(self.rows, self.cols, self.filled, self.unavailable_coords),
                data=self.data)
            warm_cmax = g_model.x[-1]
            warmstart = m.create_empty_solution()
            for i in m_range:
                for j in p_range:
                    if warm_x[i, j].x > 0.5:
                        warmstart.add_interval_var_solution(task_wraps[i][j], presence=True)
            m.set_starting_point(warmstart)
        return warm_cmax

    def merge_schedules(self, schedules):
        """
        Merge an array of schedules sequentially, ensuring that each dataframe's tasks
        start after the previous dataframe's last task finishes.
        """
        if not schedules:
            return pd.DataFrame()

        if len(schedules) == 1:
            return schedules[0].copy()

        result = schedules[0].copy()

        current_end = result['Finish'].max()

        # Process each subsequent schedule
        for i in range(1, len(schedules)):
            df = schedules[i].copy()

            # Calculate offset: Last finish + the longest possible path(extender will optimize it away)
            offset = current_end + self.cols + self.rows

            # Adjust Start and Finish times
            df['Start'] = df['Start'] + offset
            df['Finish'] = df['Finish'] + offset

            # Append the adjusted dataframe to the result
            result = pd.concat([result, df], ignore_index=True)

            # Update current end time
            current_end = result['Finish'].max()

        return result

    def run_batch(self, batch_patients_df) -> BatchResult:
        """
            Run the scheduler on a batch of patients
        """
        # Create tasks from the batch
        main_tasks = self.create_tasks(batch_patients_df)

        # Calculate ranges
        movers, lengths, ranges = self.gen_ranges(batch_patients_df, main_tasks)
        m_range, t_range, p_range, i_range = ranges

        # Initialize model and tasks
        model = CpoModel()
        main_task_intervals, tasks_by_patients = self.gen_task_vars(batch_patients_df, main_tasks, model)

        # Generate sequence variables and metadata
        (seq_tsk, meta_vis, tsks_by_meds, alt_tsks_start_point,
         ifaces, tsks_by_tiles) = self.gen_seq_vars(model, ranges, movers, main_tasks, main_task_intervals)

        # Setup time and sequences
        setup_time = self.gen_setup_time(seq_tsk, meta_vis)
        seq_mvr_tasks, seq_id_meds = self.gen_sequences_movers_meds(seq_tsk, m_range, tsks_by_meds, model)
        task_wraps, mover_patients_wraps, tile_wraps = self.gen_wrappers(
            tasks_by_patients, m_range, meta_vis, movers, model, tsks_by_tiles)

        # Add constraints
        self.add_constraints(model, ranges, seq_mvr_tasks, seq_id_meds, mover_patients_wraps, setup_time,
                             alt_tsks_start_point, main_task_intervals, seq_tsk,
                             tasks_by_patients, task_wraps, tile_wraps, ifaces)

        # Apply warmup if requested
        path_optimizer = PathOptimizer(self.rows, self.cols, self.filled, self.unavailable_coords)
        warm_cmax = self.apply_warmup(model, task_wraps, m_range, p_range, path_optimizer)

        # Solve the model and parse solution
        solution = self.solve(model, main_task_intervals, t_range)
        res, wrap_res = self.parse_solution(solution, meta_vis)

        # Reset the index
        res.sort_values('Start', inplace=True)
        res.reset_index(drop=True, inplace=True)

        return BatchResult(tasks=res, wrappers=wrap_res, metadata=meta_vis, warmup_cmax=warm_cmax)

    def run(self):
        """
            Run the scheduler on the full patient dataframe
        """
        return self.run_batch(self.patients_df)

    def run_multiple_batches(self, batch_size=None):
        """
            Run the scheduler on multiple batches of patients
        """
        if batch_size is None or batch_size >= len(self.patients_df):
            return [self.run()]

        results = []
        for i in range(0, len(self.patients_df), batch_size):
            batch_df = self.patients_df.iloc[i:i + batch_size].copy()
            batch_df.reset_index(inplace=True, drop=True)
            results.append(self.run_batch(batch_df))

        return results
