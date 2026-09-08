from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.celery_app import celery_app
from clients.tasks.base_task_client import BaseTaskClient
from clients.tasks.celery_task_client import CeleryTaskClient
from core.config import settings
from db.base_unit_of_work import BaseUnitOfWork
from db.postgresql_unit_of_work import PostgreSQLUnitOfWork
from services.configuration_service import ConfigurationService
from services.experiment_service import ExperimentService
from services.ingredient_list_service import IngredientListService
from services.layout_service import LayoutService
from services.order_list_service import OrderListService
import redis

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_uow() -> BaseUnitOfWork:
    return PostgreSQLUnitOfWork(session_factory=SessionLocal)

def get_celery_client() -> BaseTaskClient:
    redis_client = redis.from_url(settings.CELERY_BROKER_URL)
    return CeleryTaskClient(celery=celery_app,redis_client=redis_client)

def get_experiment_service(
    uow: BaseUnitOfWork = Depends(get_uow),
    celery_client: BaseTaskClient = Depends(get_celery_client)
) -> ExperimentService:
    return ExperimentService(uow=uow, task_client=celery_client)

def get_configuration_service(
    uow: BaseUnitOfWork = Depends(get_uow)
) -> ConfigurationService:
    return ConfigurationService(uow=uow)

def get_layout_service(
    uow: BaseUnitOfWork = Depends(get_uow)
) -> LayoutService:
    return LayoutService(uow=uow)

def get_order_list_service(
    uow: BaseUnitOfWork = Depends(get_uow)
) -> OrderListService:
    return OrderListService(uow=uow)

def get_ingredient_list_service(
    uow: BaseUnitOfWork = Depends(get_uow)
) -> IngredientListService:
    return IngredientListService(uow=uow)