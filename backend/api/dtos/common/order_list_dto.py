from typing import Optional, List

from pydantic import BaseModel, Field

from domain.enums import OrderListType


class OrderItemDTO(BaseModel):
    """
    Data Transfer Object representing a single item from an order.
    """
    name: str = Field(
        ...,
        min_length=1,
        description="Name of the item.",
        examples=["LISINOPRIL"]
    )
    quantity: float = Field(
        ...,
        ge=0,
        description="Quantity of the item.",
        examples=["5"]
    )


class OrderDTO(BaseModel):
    """
    Data Transfer Object representing a single order.
    """
    items: List[OrderItemDTO] = Field(
        ...,
        description="Items included in this order."
    )
    t_max: Optional[int] = Field(
        default=None,
        description="Maximum time in seconds allowed for completion of this order."
    )


class OrderListDTO(BaseModel):
    """
    Data Transfer Object representing a list of orders.
    """
    name: Optional[str] = Field(
        default=None,
        description="Name of the order list."
    )
    type: OrderListType = Field(
        ...,
        description="Type of the order list."
    )
    orders: List[OrderDTO] = Field(
        ...,
        description="Orders that are on the list."
    )
