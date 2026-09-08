from domain.enums import TileType, OrderListType
from domain.models.experiment import ExperimentDomainModel
from solvers.common.models import Schedule


def verify_obtained_schedule(data: ExperimentDomainModel, schedule: Schedule) -> bool:
    """Verifies that obtained schedule is valid for both Medicine and Perfumes.

    Args:
        data: Experiment domain model for which the schedule was created.
        schedule: Created schedule to be verified.

    Returns:
        True if the schedule is valid, False otherwise.
    """
    errors = []

    # ---------------------------------------------------------
    # 1. Group tasks by Mover for sequence and exclusivity checks
    # ---------------------------------------------------------
    movers_tasks = {}
    for task in schedule.tasks:
        movers_tasks.setdefault(task.mover_id, []).append(task)

    for mover_id, tasks in movers_tasks.items():
        tasks.sort(key=lambda t: t.start)

        prev_end = -1
        for task in tasks:
            # Check Mover-level task overlap
            if task.start < prev_end:
                errors.append(
                    f"Overlap Error: Mover {mover_id} has overlapping tasks around Start time {task.start} (Task ID: {task.task_id})."
                )
            prev_end = task.end

        # Check order-level exclusivity (orders cannot interleave on a single mover)
        order_intervals = {}
        for task in tasks:
            if task.order_id not in order_intervals:
                order_intervals[task.order_id] = {'start': task.start, 'end': task.end}
            else:
                order_intervals[task.order_id]['start'] = min(order_intervals[task.order_id]['start'], task.start)
                order_intervals[task.order_id]['end'] = max(order_intervals[task.order_id]['end'], task.end)

        sorted_orders = sorted(order_intervals.items(), key=lambda item: item[1]['start'])
        prev_order_end = -1
        prev_order_id = None

        for order_id, bounds in sorted_orders:
            if bounds['start'] < prev_order_end:
                errors.append(
                    f"Exclusivity Error: Mover {mover_id} interleaves Order {prev_order_id} and Order {order_id}."
                )
            prev_order_end = bounds['end']
            prev_order_id = order_id

    # ---------------------------------------------------------
    # 2. Tile Overlap Check (Physical collision on machines)
    # ---------------------------------------------------------
    tiles_tasks = {}
    for task in schedule.tasks:
        if task.tile.type != TileType.INTERFACE:
            coord_key = (task.tile.x, task.tile.y)
            tiles_tasks.setdefault(coord_key, []).append(task)

    for coords, tasks in tiles_tasks.items():
        tasks.sort(key=lambda t: t.start)
        prev_end = -1
        for task in tasks:
            if task.start < prev_end:
                errors.append(
                    f"Collision Error: Multiple movers are using Tile {coords} (Type: {task.tile.type.value}) at time {task.start}."
                )
            prev_end = task.end

    def get_layout_tile(x: int, y: int):
        for layout_tile in data.layout.tiles:
            if layout_tile.x == x and layout_tile.y == y:
                return layout_tile
        return None

    # ---------------------------------------------------------
    # 3. Process Task-by-Task constraints & Order constraints
    # ---------------------------------------------------------
    for task in schedule.tasks:
        idx = task.task_id

        # End - Start >= Length (Duration)
        if task.end - task.start < task.duration:
            errors.append(
                f"Time Error (Task {idx}): End ({task.end}) - Start ({task.start}) < Duration ({task.duration})."
            )

        if task.tile.type != TileType.INTERFACE:
            official_tile = get_layout_tile(task.tile.x, task.tile.y)
            if not official_tile:
                errors.append(
                    f"Bounds Error (Task {idx}): No tile exists at ({task.tile.x}, {task.tile.y}) in the layout."
                )

            # If it's a dispenser, check the drugs
            if task.tile.type == TileType.DISPENSER:

                # Length >= dosage * dispensing_time (For Medicines primarily)
                if data.order_list.type == OrderListType.MEDICINE:
                    if task.order_id < len(data.order_list.orders):
                        order = data.order_list.orders[task.order_id]
                        matched_any_drug = False
                        duration_valid = False
                        failed_durations = []

                        for item in order.items:
                            if item.name in (task.tile.dispensed_types or []):
                                matched_any_drug = True
                                min_length = item.quantity * data.configuration.dispensing_time

                                if task.duration >= min_length:
                                    duration_valid = True
                                    break
                                else:
                                    failed_durations.append(f"{item.name} (min: {min_length})")

                        if not matched_any_drug:
                            errors.append(
                                f"Prescription Error (Task {idx}): Tile dispenses {task.tile.dispensed_types}, but none are in Order {task.order_id}."
                            )
                        elif not duration_valid:
                            errors.append(
                                f"Length Error (Task {idx}): Task duration {task.duration} is too short. Failed checks: {', '.join(failed_durations)}."
                            )
                    else:
                        errors.append(
                            f"Data Error (Task {idx}): Order index {task.order_id} does not exist in data.order_list."
                        )

    # ---------------------------------------------------------
    # 4. Perfume-Specific Order Level Checks (T_max)
    # ---------------------------------------------------------
    if data.order_list.type == OrderListType.PERFUME:
        for order_id, order in enumerate(data.order_list.orders):
            order_tasks = [t for t in schedule.tasks if t.order_id == order_id]
            if not order_tasks:
                continue

            # The t_max applies from the first core ingredient dispensing (Top Notes) to the end of the capping task.
            core_tasks = [t for t in order_tasks if t.tile.type not in (TileType.INTERFACE, TileType.EMPTY)]

            if core_tasks:
                # Minimum start time among core processing tasks
                processing_start = min(t.start for t in core_tasks)
                # Maximum end time among core processing tasks
                processing_end = max(t.end for t in core_tasks)

                # Check t_max constraint
                if order.t_max is not None and (processing_end - processing_start) > order.t_max:
                    errors.append(
                        f"T_max Error: Order {order_id} exceeded its t_max! Allowed: {order.t_max}s, Actual Core Processing Time: {(processing_end - processing_start)}s."
                    )

    if not errors:
        return True
    else:
        print(f"Found {len(errors)} validation errors:\n")
        for error in errors:
            print("-", error)
        return False
