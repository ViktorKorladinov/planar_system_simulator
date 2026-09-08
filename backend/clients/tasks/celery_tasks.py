import multiprocessing
import os
import sys
import time

import requests
from billiard.exceptions import Terminated
from celery import shared_task
from celery.exceptions import Reject
from celery.signals import worker_process_init
from redis import Redis

from clients.simulator.simulator_client import SimulatorClient
from core.config import settings
from dependencies import get_uow, engine
from domain.enums import GraphType, ExperimentStatus
from solvers.factory import get_solver

redis_client = Redis.from_url(settings.CELERY_BROKER_URL)


@worker_process_init.connect
def dispose_sqlalchemy_connections(**kwargs) -> None:
    """
    This runs once per worker process when it spins up.
    It forces SQLAlchemy to create a fresh connection pool for this specific worker.
    """
    engine.dispose()


def save_gannt_charts(experiment_id: int, gantt_files: dict[GraphType, str]) -> bool:
    """Attempts to save gannt charts.

    Args:
        experiment_id: The ID of the experiment/simulation.
        gantt_files: Dictionary with gannt file type and content.

    Returns:
        True if gannt charts saved successfully, False otherwise.
    """
    if len(gantt_files) == 0:
        return True

    experiment_folder = os.path.join(settings.GRAPH_FOLDER_PATH, str(experiment_id))
    os.makedirs(experiment_folder, exist_ok=True)

    for graph_type, content in gantt_files.items():
        prefix = graph_type.value if hasattr(graph_type, 'value') else graph_type
        filename = f"{prefix.lower()}_graph.html"
        path = os.path.join(experiment_folder, filename)
        with open(path, "w", encoding="utf-8") as output_file:
            output_file.write(content)
    return True

def notify_about_experiment_status_change(experiment_id: int, status: ExperimentStatus) -> None:
    """Sends notification about experiment status change.

    Args:
        experiment_id: ID of the experiment which should be solved.
        status: The status of the experiment.
    """
    try:
        client = SimulatorClient(api_key=settings.SIMULATOR_API_KEY)
        client.notify_experiment_status_change(experiment_id, status)
    except Exception as e:
        print(f"Failed to send notification: {e}")


def run_solver(experiment_id: int):
    """Retrieves experiment data, solves experiments and saves result.

    Args:
        experiment_id: ID of the experiment which should be solved.
    """
    uow = get_uow()
    with uow:
        experiment = uow.experiment_repo.find_by_id(experiment_id)
        if not experiment:
            return
        # Ensure that process amount chosen for experiment doesn't exceed backend limit.
        if experiment.configuration.process_amount > settings.MAX_PROCESS_AMOUNT:
            experiment.configuration.process_amount = settings.MAX_PROCESS_AMOUNT
            uow.configuration_repo.update(experiment.configuration)
            uow.commit()
        experiment.mark_as_running()
        uow.experiment_repo.update(experiment)
        uow.commit()
        # Notify about changing experiment status to running.
        notify_about_experiment_status_change(experiment_id, experiment.status)
        solver = get_solver(experiment.configuration.solver_type)
        experiment_result = solver.solve(experiment)
        if experiment_result.status == ExperimentStatus.FINISHED:
            charts_saved = save_gannt_charts(experiment_id, experiment_result.gantt_files)
            if charts_saved:
                # Load fresh experiment data shortly before saving results to prevent reverting name change during solution process
                experiment = uow.experiment_repo.find_by_id(experiment_id)
                experiment.mark_as_finished()
                experiment.save_extended_result(experiment_result.result)
                uow.experiment_repo.update(experiment)
                uow.commit()
                notify_about_experiment_status_change(experiment_id, experiment.status)
        else:
            # Load fresh experiment data shortly before saving results to prevent reverting name change during solution process
            experiment = uow.experiment_repo.find_by_id(experiment_id)
            experiment.mark_as_failed()
            uow.experiment_repo.update(experiment)
            uow.commit()
            notify_about_experiment_status_change(experiment_id, experiment.status)


@shared_task(
    bind=True,
    name='tasks.solve_experiment',
    acks_late=True,
    reject_on_worker_lost=True
)
def solve_experiment_task(self, experiment_id: int):
    task_id = self.request.id
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    solver_process = multiprocessing.Process(
        target=run_solver,
        args=(experiment_id,)
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    solver_process.start()

    try:
        while solver_process.is_alive():
            if redis_client.exists(f"cancel_task:{task_id}"):
                solver_process.terminate()
                solver_process.join()
                return
            time.sleep(5)
        solver_process.join()

        if solver_process.exitcode != 0:
            raise Reject(f"Solver process terminated abnormally with exit code {solver_process.exitcode}. Requeueing.",
                         requeue=True)

    except (KeyboardInterrupt, SystemExit, Terminated):
        if solver_process.is_alive():
            solver_process.terminate()
            solver_process.join()
        raise Reject("Worker is shutting down, returning task to queue", requeue=True)

    except Exception:
        if solver_process.is_alive():
            solver_process.terminate()
            solver_process.join()
        raise
