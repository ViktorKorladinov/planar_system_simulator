from api.dtos.requests.experiment import ExperimentCreateRequestDTO
from core.config import settings
from domain.enums import ExperimentStatus, MoverMode
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel, MoverStep
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel
from mappers.domain.experiment_mapper import (
    map_experiment_create_request_dto_to_domain,
    map_experiment_matrix_create_request_to_domain,
    map_experiment_domain_to_summary_response_dto,
    map_batch_domain_to_batch_create_response_dto,
    map_batch_domain_to_summary_response_dto,
    map_batches_domain_to_paginated_get_response_dto,
    map_batch_domain_to_batch_get_response_dto,
    map_experiments_domain_to_paginated_get_response_dto,
    map_experiment_domain_to_single_create_response_dto,
    map_experiment_domain_to_single_get_response_dto,
    map_experiments_domain_to_queue_get_response_dto,
    map_experiment_domain_to_topology_info_dto,
    map_experiment_domain_to_simulation_summary_dto,
    map_experiments_domain_to_simulation_batch_response_dto,
    map_mover_step_domain_to_dto,
    get_layout_dimensions,
    map_experiment_domain_to_mover_paths_dto,
    map_experiment_domain_to_gannt_data_dto,
    extract_medicine_dict,
    extract_dispensers_dict,
    map_experiment_domain_to_simulation_get_response_dto
)
from tests.factories.experiment_factory import (
    get_batch_domain_model
)
from tests.factories.layout_factory import get_layout_domain_model, get_tile_domain_model


def test_map_experiment_create_request_dto_to_domain(
        experiment_create_request_dto: ExperimentCreateRequestDTO,
        configuration_domain_model: ConfigurationDomainModel,
        layout_domain_model: LayoutDomainModel,
        order_list_domain_model: OrderListDomainModel) -> None:
    # Act
    domain_model = map_experiment_create_request_dto_to_domain(
        dto=experiment_create_request_dto,
        configuration_domain_model=configuration_domain_model,
        layout_domain_model=layout_domain_model,
        order_list_domain_model=order_list_domain_model
    )

    # Assert
    assert domain_model.name == experiment_create_request_dto.name
    assert domain_model.status == ExperimentStatus.QUEUED
    assert domain_model.layout == layout_domain_model
    assert domain_model.configuration == configuration_domain_model
    assert domain_model.order_list == order_list_domain_model


def test_map_experiment_matrix_create_request_to_domain(
        configuration_domain_model: ConfigurationDomainModel,
        layout_domain_model: LayoutDomainModel,
        order_list_domain_model: OrderListDomainModel) -> None:
    # Act
    domain_model = map_experiment_matrix_create_request_to_domain(
        configuration_domain_model=configuration_domain_model,
        layout_domain_model=layout_domain_model,
        order_list_domain_model=order_list_domain_model
    )

    # Assert
    assert domain_model.name is None
    assert domain_model.status == ExperimentStatus.QUEUED
    assert domain_model.layout == layout_domain_model


def test_map_experiment_domain_to_summary_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_summary_response_dto(experiment_domain_model)

    # Assert
    assert dto.id == experiment_domain_model.id
    assert dto.name == experiment_domain_model.name
    assert dto.layout_name == experiment_domain_model.layout.name
    assert dto.configuration_name == experiment_domain_model.configuration.name
    assert dto.tile_amount == experiment_domain_model.layout.tile_amount


def test_map_batch_domain_to_batch_create_response_dto() -> None:
    # Arrange
    batch_domain = get_batch_domain_model()

    # Act
    dto = map_batch_domain_to_batch_create_response_dto(
        domain_model=batch_domain, created_count=1, skipped_count=0,
        estimated_time=120, errors=[], is_dry_run=False
    )

    # Assert
    assert dto.name == batch_domain.name
    assert dto.created_amount == 1
    assert len(dto.experiments) == 1
    assert dto.estimated_time == 120


def test_map_batch_domain_to_batch_create_response_dto_when_none() -> None:
    # Act
    dto = map_batch_domain_to_batch_create_response_dto(
        domain_model=None, created_count=0, skipped_count=2,
        estimated_time=0, errors=["Error"], is_dry_run=True
    )

    # Assert
    assert dto.experiments is None
    assert dto.skipped_amount == 2
    assert "Error" in dto.errors
    assert dto.is_dry_run is True


def test_map_batch_domain_to_summary_response_dto() -> None:
    # Arrange
    batch_domain = get_batch_domain_model()

    # Act
    dto = map_batch_domain_to_summary_response_dto(batch_domain)

    # Assert
    assert dto.id == batch_domain.id
    assert dto.name == batch_domain.name
    assert dto.total_experiment_amount == batch_domain.total_experiment_amount


def test_map_batches_domain_to_paginated_get_response_dto() -> None:
    # Arrange
    batch_domain = get_batch_domain_model()

    # Act
    dto = map_batches_domain_to_paginated_get_response_dto(
        domain_models=[batch_domain], page=1, size=10, total=1
    )

    # Assert
    assert dto.page == 1
    assert dto.total == 1
    assert len(dto.batches) == 1
    assert dto.batches[0].id == batch_domain.id


def test_map_batch_domain_to_batch_get_response_dto() -> None:
    # Arrange
    batch_domain = get_batch_domain_model()

    # Act
    dto = map_batch_domain_to_batch_get_response_dto(batch_domain)

    # Assert
    assert dto.id == batch_domain.id
    assert len(dto.experiments) == len(batch_domain.experiments)


def test_map_experiments_domain_to_paginated_get_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiments_domain_to_paginated_get_response_dto(
        domain_models=[experiment_domain_model], page=1, size=10, total=1
    )

    # Assert
    assert dto.page == 1
    assert dto.total == 1
    assert len(dto.experiments) == 1


def test_map_experiment_domain_to_single_create_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_single_create_response_dto(
        domain_model=experiment_domain_model, errors=[], is_dry_run=False
    )

    # Assert
    assert dto.id == experiment_domain_model.id
    assert dto.layout_id == experiment_domain_model.layout.id
    assert dto.is_dry_run is False


def test_map_experiment_domain_to_single_create_response_dto_when_none() -> None:
    # Act
    dto = map_experiment_domain_to_single_create_response_dto(
        domain_model=None, errors=["Validation error"], is_dry_run=True
    )

    # Assert
    assert dto.id is None
    assert dto.is_dry_run is True
    assert dto.errors == ["Validation error"]


def test_map_experiment_domain_to_single_get_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_single_get_response_dto(experiment_domain_model)

    # Assert
    assert dto.id == experiment_domain_model.id
    assert dto.layout_id == experiment_domain_model.layout.id


def test_map_experiments_domain_to_queue_get_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiments_domain_to_queue_get_response_dto([experiment_domain_model])

    # Assert
    assert len(dto.experiments) == 1
    assert dto.experiments[0].id == experiment_domain_model.id


def test_map_experiment_domain_to_topology_info_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_topology_info_dto(experiment_domain_model)

    # Assert
    assert dto.topology == experiment_domain_model.layout.type
    assert dto.n_tiles == experiment_domain_model.layout.tile_amount
    assert dto.n_dispensers == experiment_domain_model.layout.dispenser_amount


def test_map_experiment_domain_to_simulation_summary_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_simulation_summary_dto(experiment_domain_model)

    # Assert
    assert dto.id == experiment_domain_model.id
    assert "Simulation" in dto.name
    assert dto.dispensing_time == experiment_domain_model.configuration.dispensing_time


def test_map_experiments_domain_to_simulation_batch_response_dto(
        experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiments_domain_to_simulation_batch_response_dto(
        domain_models=[experiment_domain_model], total_pages=5, page=2, size=10
    )

    # Assert
    assert dto.total == 5
    assert dto.page == 2
    assert len(dto.items) == 1


def test_map_mover_step_domain_to_dto() -> None:
    # Arrange
    step = MoverStep(x=0, y=1, mode=MoverMode.WAIT_REST, order="order_0", rest_offset_x=1, rest_offset_y=0)

    # Act
    dto = map_mover_step_domain_to_dto(step)

    # Assert
    assert dto.x == step.x
    assert dto.y == step.y
    assert dto.mode == step.mode


def test_get_layout_dimensions() -> None:
    # Arrange
    tiles = [
        get_tile_domain_model(x=0, y=0),
        get_tile_domain_model(x=1, y=2),
        get_tile_domain_model(x=3, y=1)
    ]

    # Act
    m, n = get_layout_dimensions(tiles)

    # Assert
    assert m == 3
    assert n == 4


def test_map_experiment_domain_to_mover_paths_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_mover_paths_dto(experiment_domain_model)

    # Assert
    assert len(dto.paths) == len(experiment_domain_model.result.mover_paths)
    assert dto.m > 0
    assert dto.n > 0


def test_map_experiment_domain_to_gannt_data_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_gannt_data_dto(experiment_domain_model)

    # Assert
    assert dto.max_path == experiment_domain_model.result.max_path
    assert f"{settings.BACKEND_URL}/api/v1/simulations/{experiment_domain_model.id}/plots" == dto.api_plot_url


def test_extract_medicine_dict() -> None:
    # Arrange
    tiles = get_layout_domain_model().tiles

    # Act
    result = extract_medicine_dict(tiles)

    # Assert
    assert "interface" in result
    assert "Aspirin" in result


def test_extract_dispensers_dict() -> None:
    # Arrange
    tiles = get_layout_domain_model().tiles

    # Act
    result = extract_dispensers_dict(tiles)

    # Assert
    assert "0x0" in result
    assert result["0x0"] == "interface"
    assert "1x1" in result
    assert result["1x1"] == "mixer"


def test_map_experiment_domain_to_simulation_get_response_dto(experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    dto = map_experiment_domain_to_simulation_get_response_dto(experiment_domain_model)

    # Assert
    assert "interface" in dto.tile_type_dict
    assert "0x0" in dto.dispenser_dict
    assert dto.gantts.max_path == experiment_domain_model.result.max_path
    assert len(dto.mover_paths.paths) > 0
