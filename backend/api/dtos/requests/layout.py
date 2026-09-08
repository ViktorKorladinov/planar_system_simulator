from pydantic import BaseModel, Field

from api.dtos.common.layout_dto import LayoutDTO


class LayoutSingleCreateRequestDTO(LayoutDTO):
    """
    Data Transfer Object representing a single layout create request.
    """
    pass


class LayoutSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single layout update request.
    """
    name: str = Field(
        ...,
        description="New name of the layout."
    )
