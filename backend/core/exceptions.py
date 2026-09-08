class EntityInUseError(Exception):
    """Raised when attempting to delete an entity that is still referenced by another entity."""
    pass


class EntityNotFoundError(Exception):
    """Raised when attempting to find entity with ID which doesn't exist."""

    def __init__(self, entity_name: str, entity_id: int):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with ID {entity_id} not found.")
