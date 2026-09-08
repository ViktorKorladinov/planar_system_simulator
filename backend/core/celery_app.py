from celery import Celery

from core.config import settings

celery_app = Celery(
    "experiment_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['clients.tasks.celery_tasks']
)

# Force the worker to only process one task at a time to ensure queue fairness
celery_app.conf.update(
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True
)
