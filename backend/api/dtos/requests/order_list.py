from typing import Optional

from pydantic import BaseModel, Field

from api.dtos.common.order_list_dto import OrderListDTO


class OrderListSingleCreateRequestDTO(OrderListDTO):
    """
    Data Transfer Object representing a single order list create request.
    """
    pass


class OrderListSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single order list update request.
    """
    name: Optional[str] = Field(
        default=None,
        description="New name of the order list."
    )
