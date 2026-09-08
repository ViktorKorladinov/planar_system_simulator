from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.order_list_dto import OrderItemDTO, OrderDTO, OrderListDTO
from api.dtos.common.tile_dto import TileDTO
from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO
from api.dtos.requests.experiment import ExperimentCreateRequestDTO, ExperimentMatrixCreateRequestDTO
from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO
from api.dtos.responses.experiment import ExperimentSingleGetResponseDTO
from clients.simulator.simulator_client import SimulatorClient
from db.orm_models.base import Base
from db.orm_models.configuration import ConfigurationORM
from db.orm_models.experiment import ExperimentORM
from db.orm_models.layout import LayoutORM
from db.orm_models.order_list import OrderListORM
from dependencies import get_experiment_service, get_configuration_service, get_ingredient_list_service, \
    get_layout_service, get_order_list_service
from domain.models.common.tile import Tile
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel, MoverStep
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderItem, Order, OrderListDomainModel
from main import app
from tests.factories.configuration_factory import get_configuration_domain_model, get_configuration_orm_model, \
    get_configuration_dto, get_configuration_single_create_request_dto
from tests.factories.experiment_factory import get_experiment_domain_model, get_experiment_orm_model, \
    get_order_item_dto, get_order_item_domain_model, get_order_dto, get_order_domain_model, \
    get_experiment_create_request_dto, get_mover_step_domain_model, \
    get_experiment_single_get_response_dto, get_experiment_matrix_create_request_dto
from tests.factories.layout_factory import get_layout_domain_model, get_layout_orm_model, get_tile_dto, get_layout_dto, \
    get_layout_single_create_request_dto, get_tile_domain_model
from tests.factories.order_list_factory import get_order_list_domain_model, get_order_list_orm_model, \
    get_order_list_dto, get_order_list_single_create_request_dto

TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/test_dbname"


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, Any, None]:
    """Creates the database engine and tables once for the whole test session."""
    engine = create_engine(TEST_DATABASE_URL)

    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)

    yield engine

    # Clean up: Drop all tables when all tests are finished
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(engine: object) -> Generator[Session, Any, None]:
    """
    Creates a fresh database session for a test and rolls it back after.
    This ensures tests are fast and completely isolated from each other.
    """
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()

    # Bind the session to the connection
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    # Start a savepoint (nested transaction)
    session.begin_nested()

    yield session

    # Rollback everything that happened in the test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def reset_dependencies() -> Generator[None, Any, None]:
    """
    Automatically clears FastAPI dependency overrides after every test to ensure test isolation.
    """
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_experiment_service() -> Generator[MagicMock, None, None]:
    """
    Allows dependency injection of Mock service.
    """
    mock = MagicMock()
    app.dependency_overrides[get_experiment_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_experiment_service, None)


@pytest.fixture
def mock_configuration_service() -> Generator[MagicMock, None, None]:
    """
    Allows dependency injection of Mock service.
    """
    mock = MagicMock()
    app.dependency_overrides[get_configuration_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_configuration_service, None)


@pytest.fixture
def mock_ingredient_list_service() -> Generator[MagicMock, None, None]:
    """
    Allows dependency injection of Mock service.
    """
    mock = MagicMock()
    app.dependency_overrides[get_ingredient_list_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_ingredient_list_service, None)


@pytest.fixture
def mock_layout_service() -> Generator[MagicMock, None, None]:
    """
    Allows dependency injection of Mock service.
    """
    mock = MagicMock()
    app.dependency_overrides[get_layout_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_layout_service, None)


@pytest.fixture
def mock_order_list_service() -> Generator[MagicMock, None, None]:
    """
    Allows dependency injection of Mock service.
    """
    mock = MagicMock()
    app.dependency_overrides[get_order_list_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_order_list_service, None)


@pytest.fixture
def experiment_domain_model() -> ExperimentDomainModel:
    return get_experiment_domain_model()


@pytest.fixture
def experiment_orm_model() -> ExperimentORM:
    return get_experiment_orm_model()


@pytest.fixture
def experiment_create_request_dto() -> ExperimentCreateRequestDTO:
    return get_experiment_create_request_dto()


@pytest.fixture
def experiment_matrix_create_request_dto() -> ExperimentMatrixCreateRequestDTO:
    return get_experiment_matrix_create_request_dto()


@pytest.fixture
def experiment_single_get_response_dto() -> ExperimentSingleGetResponseDTO:
    return get_experiment_single_get_response_dto()


@pytest.fixture
def order_item_dto() -> OrderItemDTO:
    return get_order_item_dto()


@pytest.fixture
def order_item_domain_model() -> OrderItem:
    return get_order_item_domain_model()


@pytest.fixture
def order_dto() -> OrderDTO:
    return get_order_dto()


@pytest.fixture
def order_domain_model() -> Order:
    return get_order_domain_model()


@pytest.fixture
def order_list_domain_model() -> OrderListDomainModel:
    return get_order_list_domain_model()


@pytest.fixture
def order_list_orm_model() -> OrderListORM:
    return get_order_list_orm_model()


@pytest.fixture
def order_list_dto() -> OrderListDTO:
    return get_order_list_dto()


@pytest.fixture
def order_list_single_create_request_dto() -> OrderListSingleCreateRequestDTO:
    return get_order_list_single_create_request_dto()


@pytest.fixture
def mover_step_domain_model() -> MoverStep:
    return get_mover_step_domain_model()


@pytest.fixture
def configuration_domain_model() -> ConfigurationDomainModel:
    return get_configuration_domain_model()


@pytest.fixture
def configuration_orm_model() -> ConfigurationORM:
    return get_configuration_orm_model()


@pytest.fixture
def configuration_dto() -> ConfigurationDTO:
    return get_configuration_dto()


@pytest.fixture
def configuration_single_create_request_dto() -> ConfigurationSingleCreateRequestDTO:
    return get_configuration_single_create_request_dto()


@pytest.fixture
def layout_domain_model() -> LayoutDomainModel:
    return get_layout_domain_model()


@pytest.fixture
def layout_orm_model() -> LayoutORM:
    return get_layout_orm_model()


@pytest.fixture
def tile_dto() -> TileDTO:
    return get_tile_dto()


@pytest.fixture
def tile_domain_model() -> Tile:
    return get_tile_domain_model()


@pytest.fixture
def layout_dto() -> LayoutDTO:
    return get_layout_dto()


@pytest.fixture
def layout_single_create_request_dto() -> LayoutDTO:
    return get_layout_single_create_request_dto()


@pytest.fixture
def api_key() -> str:
    return "test_api_key_123"


@pytest.fixture
def simulator_client(api_key: object) -> Any:
    return SimulatorClient(api_key=api_key)


@pytest.fixture
def valid_ingredient_list_payload() -> dict:
    """Provides a valid JSON payload for creating an ingredient list."""
    return {
        "name": "Classic Perfume Base",
        "type": "perfume",
        "ingredients": [
            {
                "name": "Ethanol",
                "note_type": "primary_solvent",
                "viscosity": 1.2,
                "volatility_rank": 5
            },
            {
                "name": "Rose Oil",
                "note_type": "heart_note",
                "viscosity": 4.5,
                "volatility_rank": 3
            }
        ]
    }


@pytest.fixture
def valid_layout_payload() -> dict:
    """Provides a valid JSON payload for creating a layout."""
    return {
        "name": "Standard Line Layout",
        "type": "line",
        "tiles": [
            {
                "type": "interface",
                "x": 0,
                "y": 0
            },
            {
                "type": "dispenser",
                "dispensed_types": ["Aspirin"],
                "x": 1,
                "y": 0
            }
        ],
        "ingredient_list_id": None,
        "ingredient_list": {
            "name": "Classic Perfume Base",
            "type": "medicine",
            "ingredients": [
                {
                    "name": "Aspirin",
                    "note_type": "primary_solvent",
                    "viscosity": None,
                    "volatility_rank": None
                }
            ]
        }
    }


@pytest.fixture
def valid_order_list_payload() -> dict:
    """Provides a valid JSON payload for creating an order list."""
    return {
        "name": "Standard Medicine Orders",
        "type": "medicine",
        "orders": [
            {
                "items": [
                    {"name": "Aspirin", "quantity": 10},
                    {"name": "Ibuprofen", "quantity": 5}
                ],
                "t_max": None
            }
        ]
    }
