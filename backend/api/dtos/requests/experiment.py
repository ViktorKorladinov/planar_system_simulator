from typing_extensions import Self
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.order_list_dto import OrderListDTO


class ExperimentCreateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single experiment create request.
    """
    name: Optional[str] = Field(
        default=None,
        description="Name of the experiment."
    )
    layout_id: Optional[int] = Field(
        default=None,
        description="ID of the layout which should be used for the experiment."
    )
    layout: Optional[LayoutDTO] = Field(
        default=None,
        description="Layout which should be used for the experiment."
    )
    configuration_id: Optional[int] = Field(
        default=None,
        description="ID of the configuration which should be used for the experiment."
    )
    configuration: Optional[ConfigurationDTO] = Field(
        default=None,
        description="Configuration which should be used for the experiment."
    )
    order_list_id: Optional[int] = Field(
        default=None,
        description="ID of the order list which should be used for the experiment."
    )
    order_list: Optional[OrderListDTO] = Field(
        default=None,
        description="Orders that should be completed in this experiment."
    )

    # Ensure that ID or object is provided for layout and configuration
    @model_validator(mode='after')
    def validate_dependencies(self) -> Self:
        has_layout_id = self.layout_id is not None
        has_layout = self.layout is not None
        if has_layout_id == has_layout:
            raise ValueError("Must provide exactly one of 'layout_id' OR 'layout' object.")

        has_config_id = self.configuration_id is not None
        has_config = self.configuration is not None
        if has_config_id == has_config:
            raise ValueError("Must provide exactly one of 'configuration_id' OR 'configuration' object.")

        has_order_list_id = self.order_list_id is not None
        has_order_list = self.order_list is not None
        if has_order_list_id == has_order_list:
            raise ValueError("Must provide exactly one of 'order_list_id' OR 'order_list' object.")
        return self


class ExperimentSingleCreateRequestDTO(ExperimentCreateRequestDTO):
    """
    Data Transfer Object representing a single experiment create request.
    """
    pass


class ExperimentSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single experiment update request.
    """
    name: str = Field(
        ...,
        description="New name of the experiment."
    )


class ExperimentBatchCreateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a batch create request with experiments.
    """
    name: Optional[str] = Field(
        ...,
        description="New name of the batch."
    )
    experiments: List[ExperimentCreateRequestDTO] = Field(
        ...,
        description="The batch of experiments to create."
    )


class ExperimentBatchSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single batch update request.
    """
    name: str = Field(
        ...,
        description="New name of the batch."
    )


class ExperimentMatrixCreateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a matrix create request with experiments.
    """
    name: Optional[str] = Field(
        ...,
        description="Prefix for the name of the experiment."
    )
    layout_ids: Optional[List[int]] = Field(
        ...,
        description="IDs of layouts which should be used for experiment creation."
    )
    layouts: Optional[List[LayoutDTO]] = Field(
        ...,
        description="Layouts which should be used for experiment creation."
    )
    configuration_ids: Optional[List[int]] = Field(
        ...,
        description="IDs of configurations which should be used for experiment creation."
    )
    configurations: Optional[List[ConfigurationDTO]] = Field(
        ...,
        description="Configurations which should be used for experiment creation."
    )
    order_list_ids: Optional[List[int]] = Field(
        ...,
        description="IDs of order lists which should be used for experiment creation."
    )
    order_lists: Optional[List[OrderListDTO]] = Field(
        ...,
        description="Order lists which should be used for experiment creation."
    )

    # Ensure that at least 1 layout, 1 configuration and 1 order list is provided.
    @model_validator(mode='after')
    def validate_dependencies(self) -> Self:
        has_layout_id = self.layout_ids is not None and len(self.layout_ids) > 0
        has_layout = self.layouts is not None and len(self.layouts) > 0
        if not has_layout_id and not has_layout:
            raise ValueError("Must provide at least one of 'layout_id' OR 'layout' object.")

        has_config_id = self.configuration_ids is not None and len(self.configuration_ids) > 0
        has_config = self.configurations is not None and len(self.configurations) > 0
        if not has_config_id and not has_config:
            raise ValueError("Must provide at least one of 'configuration_id' OR 'configuration' object.")

        has_order_list_id = self.order_list_ids is not None and len(self.order_list_ids) > 0
        has_order_list = self.order_lists is not None and len(self.order_lists) > 0
        if not has_order_list_id and not has_order_list:
            raise ValueError("Must provide at least one of 'order_list_id' OR 'order_list' object.")
        return self
