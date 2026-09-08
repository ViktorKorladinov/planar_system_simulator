from datetime import datetime
from typing import List, Optional

from pydantic import Field, BaseModel

from api.dtos.common.order_list_dto import OrderListDTO, OrderDTO
from domain.enums import OrderListType


class OrderListResponseDTO(OrderListDTO):
    id: int = Field(
        ...,
        description='ID of the order list.'
    )
    order_amount: int = Field(
        ...,
        description='Order amount.'
    )
    created_at: datetime = Field(
        default=None,
        description="Date of the order list creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the order list update."
    )


class OrderListSingleCreateResponseDTO(BaseModel):
    """
    Data Transfer Object representing a single order list create response.
    """
    id: Optional[int] = Field(
        default=None,
        description='ID of the order list.'
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Name of the order list."
    )
    type: Optional[OrderListType] = Field(
        default=None,
        description="Type of the order list."
    )
    orders: Optional[List[OrderDTO]] = Field(
        default=None,
        description="Orders that are on the list."
    )
    order_amount: Optional[int] = Field(
        default=None,
        description='Order amount.'
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )
    is_dry_run: bool = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class OrderListSingleGetResponseDTO(OrderListResponseDTO):
    """
    Data Transfer Object representing a single order list get response.
    """
    pass


class OrderListShortResponseDTO(BaseModel):
    """
    Data Transfer Object representing a short order list response.
    """
    id: int = Field(
        ...,
        description='ID of the order list.'
    )
    name: str = Field(
        default=None,
        min_length=1,
        description="Name of the order list."
    )
    type: OrderListType = Field(
        ...,
        description="Type of the order list."
    )
    order_amount: int = Field(
        ...,
        description='Order amount.'
    )
    created_at: datetime = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )


class OrderListBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a batch order list get response.
    """
    total: int = Field(
        ...,
        description="Total amount of pages."
    )
    page: int = Field(
        ...,
        description="Page number."
    )
    size: int = Field(
        ...,
        description="Amount of order lists on the page."
    )
    order_lists: List[OrderListShortResponseDTO] = Field(
        ...,
        description='Summary of order lists.'
    )
