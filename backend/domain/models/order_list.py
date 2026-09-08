from typing_extensions import Self
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import TileType, OrderListType


class OrderItem(BaseModel):
    """
    Immutable value object representing a single item from an order.
    """
    model_config = ConfigDict(frozen=True)

    name: str = Field(
        ...,
        min_length=1,
        description="Name of the ordered item."
    )
    quantity: float = Field(
        ...,
        ge=0,
        description="Quantity of the ordered item."
    )

    # Ensure that item name doesn't collide with tile types.
    @model_validator(mode='after')
    def validate_item_name(self) -> Self:
        if self.name == TileType.DISPENSER.value:
            raise ValueError(f"Name {TileType.DISPENSER.value} for order item is forbidden.")
        if self.name == TileType.EMPTY.value:
            raise ValueError(f"Name {TileType.EMPTY.value} for order item is forbidden.")
        if self.name == TileType.BLOCKED.value:
            raise ValueError(f"Name {TileType.BLOCKED.value} for order item is forbidden.")
        if self.name == TileType.INTERFACE.value:
            raise ValueError(f"Name {TileType.INTERFACE.value} for order item is forbidden.")
        return self


class Order(BaseModel):
    """
    Immutable value object representing a single order.
    """
    model_config = ConfigDict(frozen=True)

    items: List[OrderItem] = Field(
        ...,
        description="Items included in this order."
    )
    t_max: Optional[int] = Field(
        default=None,
        description="Maximum time in seconds allowed for completion of this order."
    )


class OrderListDomainModel(BaseModel):
    """
    Domain model representing list of orders.
    """
    id: Optional[int] = None
    name: Optional[str] = Field(
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
        description="Order amount of the order."
    )
    orders: List[Order] = Field(
        ...,
        description="Orders that are on the list."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the update."
    )

    # Ensure that orders contain required fields for chosen order list type.
    @model_validator(mode='after')
    def validate_orders(self) -> Self:
        if self.type == OrderListType.PERFUME:
            for order in self.orders:
                if order.t_max is None:
                    raise ValueError(f"T max is required for each order when order list type Perfume is chosen.")
        return self

    # Ensure that medicine order list contains integer values for quantity.
    @model_validator(mode='after')
    def validate_quantities(self) -> Self:
        for order in self.orders:
            if self.type == OrderListType.MEDICINE:
                for item in order.items:
                    if item.quantity <= 0:
                        raise ValueError(f"Medicine orders must have a quantity greater than 0.")
                    if not item.quantity.is_integer():
                        raise ValueError(f"Medicine orders must use whole numbers for quantities.")

        return self

    # Ensure that only quantity for mixer and capper can be 0.
    @model_validator(mode='after')
    def validate_zero_quantities(self) -> Self:
        for order in self.orders:
            for item in order.items:
                if item.quantity == 0 and item.name != TileType.MIXER.value and item.name != TileType.CAPPER.value:
                    raise ValueError(f"Zero quantities are allowed only for Mixer and Capper.")
        return self
