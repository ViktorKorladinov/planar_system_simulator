from datetime import datetime, timezone
from typing import List

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.order_list_dto import OrderDTO, OrderItemDTO, OrderListDTO
from api.dtos.common.tile_dto import TileDTO
from api.dtos.requests.experiment import ExperimentCreateRequestDTO, ExperimentMatrixCreateRequestDTO
from api.dtos.responses.experiment import ExperimentFullResponseDTO, \
    ExperimentSingleGetResponseDTO
from db.orm_models.batch import BatchORM
from db.orm_models.experiment import ExperimentORM
from domain.enums import TileType, MoverMode, ExperimentStatus, LayoutType, SolverType
from domain.models.batch import BatchDomainModel
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel, MoverStep, Result
from domain.models.order_list import Order, OrderItem
from tests.factories.configuration_factory import get_configuration_domain_model, get_configuration_orm_model, \
    get_configuration_dto
from tests.factories.ingredient_list_factory import get_ingredient_list_dto
from tests.factories.layout_factory import get_layout_domain_model, get_layout_orm_model, get_layout_dto
from tests.factories.order_list_factory import get_order_list_domain_model, get_order_list_orm_model, get_order_list_dto


def get_experiment_create_request_dto(
        name: str = "Crazy Experiment"
) -> ExperimentCreateRequestDTO:
    """Factory method to return a create request DTO.

    Args:
        name: Name of the experiments, defaults to "Crazy Experiment".

    Returns:
        Create request DTO.
    """
    return ExperimentCreateRequestDTO(
        name=name,
        layout_id=1,
        configuration_id=2,
        order_list_id=3
    )


def _get_order_domain_models() -> List[Order]:
    """Returns list of Order domain models.
    Returns:
        List of Order domain models.
    """
    return [
        Order(items=[OrderItem(name="Aspirin", quantity=3), OrderItem(name="Lisinopril", quantity=1)]),
        Order(items=[OrderItem(name="Aspirin", quantity=3)]),
        Order(items=[OrderItem(name="Aspirin", quantity=2), OrderItem(name="Lisinopril", quantity=2)])
    ]


def _get_result_domain_model() -> Result:
    """Returns Result domain model.

    Returns:
        Result domain model.
    """
    return Result(
        mover_paths=[[
            MoverStep(x=0, y=1, mode=MoverMode.TRANSIT, order="order_0", rest_offset_x=1, rest_offset_y=0),
            MoverStep(x=0, y=1, mode=MoverMode.WAIT_REST, order="order_0", rest_offset_x=1, rest_offset_y=0)
        ]],
        max_path=4,
        color_dict={"order_1": "blue", "order_2": "red"}
    )


def get_experiment_domain_model(
        experiment_id: int = 1,
        experiment_name: str = "Important Experiment",
        batch_id: int = 5,
        batch_name: str = "Mega Batch",
        layout_id: int = 2,
        layout_name: str = "Small Layout",
        layout_type: LayoutType = LayoutType.CUSTOM,
        status: ExperimentStatus = ExperimentStatus.FINISHED,
        tiles: List[Tile] = None,
        configuration_id: int = 3,
        configuration_name: str = "Test Config",
        solver_type: SolverType = SolverType.CPLEX_PERFUMES,
        interface_time: int = 3,
        dispensing_time: int = 1,
        mover_amount: int = 4,
        time_limit: int = 60,
        process_amount: int = 3,
        warmup: bool = None,
        batch_size: int = None,
        task_id: str = "celery-task-id-6",
        created_at: datetime = datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        updated_at: datetime = datetime(year=2026, month=2, day=25, hour=15, minute=45, second=10, tzinfo=timezone.utc)
) -> ExperimentDomainModel:
    """Factory method to return an experiment domain model.

    Args:
        experiment_id: Experiment ID. Defaults to 1.
        experiment_name: Experiment name. Defaults to "Important Experiment".
        batch_id: ID of the batch to which experiment belongs. Defaults to 5.
        batch_name: Name of the batch to which experiment belongs. Defaults to "Mega Batch".
        layout_id: Layout ID. Defaults to 2.
        layout_name: Layout name. Defaults to "Small Layout".
        configuration_id: Configuration ID. Defaults to 3.
        configuration_name: Configuration name. Defaults to "Test Config".
        status: Experiment status. Defaults to ExperimentStatus.FINISHED.
        layout_type: Layout type. Defaults to LayoutType.DOUBLE_LINE.
        tiles: List of tiles.
        solver_type: Solver type. Defaults to SolverType.CPLEX.
        interface_time: Interface time. Defaults to 3.
        dispensing_time: Dispensing time. Defaults to 1.
        mover_amount: Mover amount. Defaults to 4.
        time_limit: Time limit. Defaults to 60.
        process_amount: Process amount. Defaults to 3.
        warmup: Warmup. Defaults to None.
        batch_size: Batch size. Defaults to None.
        task_id: Celery task ID. Defaults to "celery-task-id-6".
        created_at: Creation time. Defaults to 2026-01-13-00-00.
        updated_at: Update time. Defaults to 2026-02-25-45-10.

    Returns:
        Experiment domain model.
    """
    layout = get_layout_domain_model(id=layout_id, name=layout_name, type=layout_type, tiles=tiles)
    configuration = get_configuration_domain_model(id=configuration_id, name=configuration_name,
                                                   solver_type=solver_type, interface_time=interface_time,
                                                   dispensing_time=dispensing_time, mover_amount=mover_amount,
                                                   time_limit=time_limit, process_amount=process_amount, warmup=warmup,
                                                   batch_size=batch_size)
    order_list = get_order_list_domain_model()
    result = _get_result_domain_model()
    return ExperimentDomainModel(
        id=experiment_id,
        name=experiment_name,
        batch_id=batch_id,
        batch_name=batch_name,
        status=status,
        layout=layout,
        configuration=configuration,
        order_list=order_list,
        result=result,
        created_at=created_at,
        updated_at=updated_at,
        task_id=task_id
    )


def get_experiment_orm_model(
        experiment_id: int = 1,
        experiment_name: str = "Important Experiment",
        status: ExperimentStatus = ExperimentStatus.FINISHED,
        task_id: str = "celery-task-id-6",
        created_at: datetime = datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        updated_at: datetime = datetime(year=2026, month=2, day=25, hour=15, minute=45, second=10, tzinfo=timezone.utc)
) -> ExperimentORM:
    """Factory method to return an experiment domain model.

    Args:
        experiment_id: Experiment ID. Defaults to 1.
        experiment_name: Experiment name. Defaults to "Important Experiment".
        status: Experiment status. Defaults to ExperimentStatus.FINISHED.
        task_id: Celery task ID. Defaults to "celery-task-id-6".
        created_at: Creation time. Defaults to 2026-01-13-00-00.
        updated_at: Update time. Defaults to 2026-02-25-45-10.

    Returns:
        Experiment ORM model.
    """
    configuration_orm_model = get_configuration_orm_model()
    layout_orm_model = get_layout_orm_model()
    order_list_orm_model = get_order_list_orm_model()
    return ExperimentORM(
        id=experiment_id,
        name=experiment_name,
        status=status,
        layout_id=layout_orm_model.id,
        layout=layout_orm_model,
        configuration_id=configuration_orm_model.id,
        configuration=configuration_orm_model,
        order_list_id=order_list_orm_model.id,
        order_list=order_list_orm_model,
        result=_get_result_domain_model().model_dump(mode='json'),
        created_at=created_at,
        updated_at=updated_at,
        task_id=task_id,
        batch_id=5
    )


def get_order_item_dto() -> OrderItemDTO:
    """Returns order item DTO.

    Returns:
        Order item DTO.
    """
    return OrderItemDTO(
        name="Aspirin",
        quantity=5
    )


def get_order_item_domain_model() -> OrderItem:
    """Returns order item domain model.

    Returns:
        Order item domain model.
    """
    return OrderItem(
        name="Aspirin",
        quantity=5
    )


def get_order_dto() -> OrderDTO:
    """Returns order item DTO.

    Returns:
        Order item DTO.
    """
    return OrderDTO(
        items=[
            OrderItemDTO(
                name="Aspirin",
                quantity=4),
            OrderItemDTO(
                name="Lisinopril",
                quantity=3)
        ]
    )


def get_order_domain_model() -> Order:
    """Returns order domain model.

    Returns:
        Order domain model.
    """
    return Order(
        items=[
            OrderItem(
                name="Aspirin",
                quantity=5),
            OrderItem(
                name="Lisinopril",
                quantity=10)
        ]
    )


def get_mover_step_domain_model() -> MoverStep:
    """Returns mover step domain model.

    Returns:
        Mover step domain model.
    """
    return MoverStep(
        x=0,
        y=1,
        mode=MoverMode.WAIT_REST,
        order="order_0",
        rest_offset_x=1,
        rest_offset_y=0
    )


def get_experiment_matrix_create_request_dto(
        name_prefix="Batch Experiment"
) -> ExperimentMatrixCreateRequestDTO:
    """Returns experiment matrix create request DTO.

    Args:
        name_prefix: Name prefix. Defaults to "Batch Experiment".

    Returns:
        Matrix create request DTO.
    """
    return ExperimentMatrixCreateRequestDTO(
        name=name_prefix,
        layout_ids=[1, 2, 3],
        configuration_ids=[4, 5, 6],
        order_list_ids=[7, 8, 9],
        layouts=[],
        configurations=[],
        order_lists=[]
    )


def get_experiment_full_response_dto(
        experiment_id: int = 1,
        name: str = 'Main Experiment',
        layout_id: int = 2,
        configuration_id: int = 2,
        layout: LayoutDTO = None,
        configuration: ConfigurationDTO = None,
        order_list: OrderListDTO = None,
        status: ExperimentStatus = ExperimentStatus.FINISHED,
        created_at: datetime = datetime(year=2026, month=1, day=13, hour=13, minute=00, second=00),
        updated_at: datetime = datetime(year=2026, month=2, day=25, hour=15, minute=45, second=10)
) -> ExperimentFullResponseDTO:
    """Factory method to return an experiment full response DTO.

    Args:
        experiment_id: Experiment ID. Defaults to 1.
        name: Experiment name. Defaults to "Important Experiment".
        layout_id: Layout ID. Defaults to 2.
        layout: Layout.
        configuration_id: Configuration ID. Defaults to 3.
        configuration: Configuration.
        status: Experiment status. Defaults to ExperimentStatus.FINISHED.
        order_list: List of orders.
        created_at: Creation time. Defaults to 2026-01-13-00-00.
        updated_at: Update time. Defaults to 2026-02-25-45-10.

        Returns:
            Experiment full response DTO.
        """
    if configuration is None:
        configuration = get_configuration_dto()
    if layout is None:
        layout = get_layout_dto()
    if order_list is None:
        order_list = get_order_list_dto()
    ingredient_list = get_ingredient_list_dto()
    return ExperimentFullResponseDTO(
        id=experiment_id,
        name=name,
        layout_id=layout_id,
        layout=layout,
        configuration_id=configuration_id,
        configuration=configuration,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        order_list=order_list,
        batch_id=5,
        batch_name="Small Batch",
        ingredient_list_id=3,
        ingredient_list=ingredient_list,
        order_list_id=4
    )


def get_experiment_single_get_response_dto() -> ExperimentSingleGetResponseDTO:
    """Returns experiment single get response DTO.

    Returns:
       Experiment single get response DTO.
    """
    return ExperimentSingleGetResponseDTO(**get_experiment_full_response_dto().model_dump())


def get_batch_domain_model(id: int = 5, name: str = "Small Batch") -> BatchDomainModel:
    return BatchDomainModel(
        id=id,
        name=name,
        total_experiment_amount=1,
        running_experiment_amount=0,
        queued_experiment_amount=0,
        failed_experiment_amount=0,
        finished_experiment_amount=1,
        created_at=datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        updated_at=datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        experiments=[get_experiment_domain_model(experiment_id=1, batch_id=id, batch_name=name)]
    )


def get_batch_orm_model(id: int = 5, name: str = "Small Batch") -> BatchORM:
    return BatchORM(
        id=id,
        name=name,
        total_experiment_amount=1,
        running_experiment_amount=0,
        queued_experiment_amount=0,
        failed_experiment_amount=0,
        finished_experiment_amount=1,
        created_at=datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        updated_at=datetime(year=2026, month=1, day=13, hour=13, minute=0, second=0, tzinfo=timezone.utc),
        experiments=[get_experiment_orm_model(experiment_id=1)]
    )
