from celery import Celery
from redis import Redis

from clients.tasks.base_task_client import BaseTaskClient


class CeleryTaskClient(BaseTaskClient):
    def __init__(self, celery: Celery, redis_client: Redis):
        self.celery = celery
        self.redis_client = redis_client

    def enqueue_experiment(self, experiment_id: int) -> str:
        result = self.celery.send_task(
            'tasks.solve_experiment',
            args=[experiment_id]
        )
        return result.id

    def cancel_experiment(self, task_id: str) -> None:
        self.celery.control.revoke(task_id)
        self.redis_client.setex(f"cancel_task:{task_id}", 3600, "1")
