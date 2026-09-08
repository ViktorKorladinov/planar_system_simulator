from unittest.mock import MagicMock

from clients.tasks.celery_task_client import CeleryTaskClient


def test_enqueue_experiment() -> None:
    # Arrange
    mock_celery = MagicMock()
    mock_redis = MagicMock()

    mock_signature = MagicMock()
    mock_celery.signature.return_value = mock_signature

    mock_task_result = MagicMock()
    mock_task_result.id = "test-task-id-123"
    mock_celery.send_task.return_value = mock_task_result

    client = CeleryTaskClient(celery=mock_celery, redis_client=mock_redis)

    # Act
    result = client.enqueue_experiment(experiment_id=10)

    # Assert
    assert result == "test-task-id-123"
    mock_celery.send_task.assert_called_once_with(
        'tasks.solve_experiment',
        args=[10]
    )


def test_cancel_experiment() -> None:
    # Arrange
    mock_celery = MagicMock()
    mock_redis = MagicMock()
    client = CeleryTaskClient(celery=mock_celery, redis_client=mock_redis)
    task_id = "test-task-id-123"

    # Act
    client.cancel_experiment(task_id)

    # Assert
    mock_celery.control.revoke.assert_called_once_with(task_id)
    mock_redis.setex.assert_called_once_with(f"cancel_task:{task_id}", 3600, "1")
