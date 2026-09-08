import os
from unittest.mock import patch, MagicMock, mock_open

from core.celery_app import celery_app
from domain.enums import ExperimentStatus, GraphType
from domain.models.experiment import ExperimentDomainModel

celery_app.conf.update(task_always_eager=True)

MODULE_PATH = 'clients.tasks.celery_tasks'


@patch(f'{MODULE_PATH}.SimulatorClient')
@patch(f'{MODULE_PATH}.get_uow')
@patch(f'{MODULE_PATH}.get_solver')
@patch(f'{MODULE_PATH}.save_gannt_charts')
@patch(f'{MODULE_PATH}.settings')
def test_run_solver_success(
        mock_settings,
        mock_save_gantt,
        mock_get_solver,
        mock_get_uow,
        mock_sim_client,
        experiment_domain_model: ExperimentDomainModel
) -> None:
    # Arrange
    mock_settings.MAX_PROCESS_AMOUNT = 4
    experiment_domain_model.configuration.process_amount = 2

    # Configure UoW Context Manager
    mock_uow = MagicMock()
    mock_get_uow.return_value = mock_uow
    mock_uow.__enter__.return_value = mock_uow
    mock_uow.experiment_repo.find_by_id.return_value = experiment_domain_model

    # Configure Solver Result
    mock_solver = MagicMock()
    mock_result = MagicMock()

    valid_result_object = experiment_domain_model.result
    mock_result.result = valid_result_object

    mock_result.gantt_files = {GraphType.DISPENSED_TYPE: "html_content"}
    mock_result.status = ExperimentStatus.FINISHED
    mock_solver.solve.return_value = mock_result
    mock_get_solver.return_value = mock_solver

    mock_save_gantt.return_value = True

    # Act
    from clients.tasks.celery_tasks import run_solver
    run_solver(experiment_id=1)

    # Assert
    mock_solver.solve.assert_called_once_with(experiment_domain_model)
    mock_save_gantt.assert_called_once_with(1, {GraphType.DISPENSED_TYPE: "html_content"})

    assert experiment_domain_model.status == ExperimentStatus.FINISHED
    assert experiment_domain_model.result == valid_result_object

    # Verify DB commits (once for RUNNING, once for FINISHED)
    assert mock_uow.experiment_repo.update.call_count == 2
    assert mock_uow.commit.call_count == 2


@patch(f'{MODULE_PATH}.SimulatorClient')
@patch(f'{MODULE_PATH}.get_uow')
@patch(f'{MODULE_PATH}.get_solver')
@patch(f'{MODULE_PATH}.settings')
def test_run_solver_process_amount_capped(
        mock_settings,
        mock_get_solver,
        mock_get_uow,
        mock_sim_client,
        experiment_domain_model: ExperimentDomainModel
) -> None:
    # Arrange
    mock_settings.MAX_PROCESS_AMOUNT = 4
    experiment_domain_model.configuration.process_amount = 10  # Exceeds limit

    mock_uow = MagicMock()
    mock_get_uow.return_value = mock_uow
    mock_uow.__enter__.return_value = mock_uow
    mock_uow.experiment_repo.find_by_id.return_value = experiment_domain_model

    mock_solver = MagicMock()
    mock_result = MagicMock()
    mock_result.status = ExperimentStatus.FAILED
    mock_solver.solve.return_value = mock_result
    mock_get_solver.return_value = mock_solver

    # Act
    from clients.tasks.celery_tasks import run_solver
    run_solver(experiment_id=1)

    # Assert
    assert experiment_domain_model.configuration.process_amount == 4
    mock_uow.configuration_repo.update.assert_called_once_with(experiment_domain_model.configuration)
    assert experiment_domain_model.status == ExperimentStatus.FAILED


@patch(f'{MODULE_PATH}.SimulatorClient')
@patch(f'{MODULE_PATH}.get_uow')
@patch(f'{MODULE_PATH}.get_solver')
@patch(f'{MODULE_PATH}.settings')
def test_run_solver_failed(
        mock_settings,
        mock_get_solver,
        mock_get_uow,
        mock_sim_client,
        experiment_domain_model: ExperimentDomainModel
) -> None:
    # Arrange
    mock_settings.MAX_PROCESS_AMOUNT = 4

    mock_uow = MagicMock()
    mock_get_uow.return_value = mock_uow
    mock_uow.__enter__.return_value = mock_uow
    mock_uow.experiment_repo.find_by_id.return_value = experiment_domain_model

    mock_solver = MagicMock()
    mock_result = MagicMock()
    mock_result.status = ExperimentStatus.FAILED
    mock_solver.solve.return_value = mock_result
    mock_get_solver.return_value = mock_solver

    # Act
    from clients.tasks.celery_tasks import run_solver
    run_solver(experiment_id=1)

    # Assert
    assert experiment_domain_model.status == ExperimentStatus.FAILED
    mock_uow.experiment_repo.update.assert_called_with(experiment_domain_model)


def test_save_gannt_charts_empty() -> None:
    from clients.tasks.celery_tasks import save_gannt_charts
    # Act
    result = save_gannt_charts(1, {})
    # Assert
    assert result is True


@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
@patch(f"{MODULE_PATH}.settings")
def test_save_gannt_charts_with_data(mock_settings: object, mock_file: object, mock_makedirs: object) -> None:
    from clients.tasks.celery_tasks import save_gannt_charts

    # Arrange
    mock_settings.GRAPH_FOLDER_PATH = "/tmp/graphs"
    mock_graph_type = MagicMock()
    mock_graph_type.value = "MACHINES"
    gantt_files = {mock_graph_type: "<html>content</html>"}

    # Act
    result = save_gannt_charts(99, gantt_files)

    # Assert
    assert result is True
    mock_makedirs.assert_called_once_with(os.path.join("/tmp/graphs", "99"), exist_ok=True)
    expected_path = os.path.join("/tmp/graphs", "99", "machines_graph.html")
    mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
    mock_file().write.assert_called_once_with("<html>content</html>")


@patch(f"{MODULE_PATH}.redis_client")
@patch(f"{MODULE_PATH}.time.sleep", return_value=None)
@patch(f"{MODULE_PATH}.multiprocessing.Process")
def test_solve_experiment_task_normal_completion(mock_process_class: object, mock_sleep: object,
                                                 mock_redis_client: object) -> None:
    from clients.tasks.celery_tasks import solve_experiment_task

    # Arrange
    mock_process_instance = MagicMock()
    mock_process_class.return_value = mock_process_instance
    mock_process_instance.is_alive.side_effect = [True, False]
    mock_redis_client.exists.return_value = False

    # Act
    solve_experiment_task.apply(args=[10], task_id="task-id-789")

    # Assert
    mock_process_instance.start.assert_called_once()
    mock_redis_client.exists.assert_called_once_with("cancel_task:task-id-789")
    mock_process_instance.join.assert_called_once()
    mock_process_instance.terminate.assert_not_called()


@patch(f"{MODULE_PATH}.redis_client")
@patch(f"{MODULE_PATH}.time.sleep", return_value=None)
@patch(f"{MODULE_PATH}.multiprocessing.Process")
def test_solve_experiment_task_cancelled(mock_process_class: object, mock_sleep: object,
                                         mock_redis_client: object) -> None:
    from clients.tasks.celery_tasks import solve_experiment_task

    # Arrange
    mock_process_instance = MagicMock()
    mock_process_class.return_value = mock_process_instance
    mock_process_instance.is_alive.return_value = True
    mock_redis_client.exists.return_value = True

    # Act
    solve_experiment_task.apply(args=[10], task_id="task-id-789")

    # Assert
    mock_process_instance.start.assert_called_once()
    mock_process_instance.terminate.assert_called_once()
    mock_process_instance.join.assert_called_once()
