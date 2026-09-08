from pydantic import BaseModel, Field

from api.dtos.common.configuration_dto import ConfigurationDTO


class ConfigurationSingleCreateRequestDTO(ConfigurationDTO):
    """
    Data Transfer Object representing a single configuration create request.
    """
    pass


class ConfigurationSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single configuration update request.
    """
    name: str = Field(
        ...,
        description="New name of the configuration."
    )
