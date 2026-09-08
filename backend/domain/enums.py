from enum import Enum, IntEnum


class SolverType(str, Enum):
    """The supported solvers for experiments."""
    CPLEX_MEDICINE = "cplex_medicine"
    CPLEX_PERFUMES = "cplex_perfumes"
    HEXALY = "hexaly"


class ExperimentStatus(str, Enum):
    """Represents possible states of an experiment."""
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class LayoutType(str, Enum):
    """The supported layout types."""
    SQUARE = "square"
    LINE = "line"
    DOUBLE_LINE = "double_line"
    RING = "ring"
    CUSTOM = "custom"


class TileType(Enum):
    """Represents known tile types with special functionality."""
    INTERFACE = "interface"
    BLOCKED = "blocked"
    EMPTY = "empty"
    DISPENSER = "dispenser"
    MIXER = "mixer"
    CAPPER = "capper"


class NoteType(Enum):
    """Represents note types used for ingredients."""
    BASE_NOTE = "base_note"
    HEART_NOTE = "heart_note"
    TOP_NOTE = "top_note"
    PRIMARY_SOLVENT = "primary_solvent"
    SECONDARY_SOLVENT = "secondary_solvent"


class NotePhase(IntEnum):
    """Represents phase assignment based on note type."""
    BASE_NOTE = 1
    HEART_NOTE = 1
    TOP_NOTE = 2
    PRIMARY_SOLVENT = 4
    SECONDARY_SOLVENT = 5


class MoverMode(str, Enum):
    """Represents possible mover modes."""
    WAIT_REST = "wait_rest"
    LOADING = "loading"
    TRANSIT = "transit"
    EXTENSION = "e"


class GraphType(str, Enum):
    """Represents possible graph types."""
    DISPENSED_TYPE = "dispensed_type"
    ORDER = "order"
    TILE = "tile"


class SortDirection(str, Enum):
    """Represents possible sort directions."""
    ASC = "asc"
    DESC = "desc"


class ExperimentSortField(str, Enum):
    NAME = "name"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STARTED_AT = "started_at"
    FINISHED_AT = "finished_at"
    TILE_AMOUNT = "tile_amount"
    INTERFACE_AMOUNT = "interface_amount"
    DISPENSER_AMOUNT = "dispenser_amount"
    LAYOUT_TYPE = "layout_type"
    LAYOUT_NAME = "layout_name"
    CONFIGURATION_NAME = "configuration_name"
    SOLVER_TYPE = "solver_type"
    MOVER_AMOUNT = "mover_amount"
    TIME_LIMIT = "time_limit"
    PROCESS_AMOUNT = "process_amount"
    BATCH_SIZE = "batch_size"
    WARMUP = "warmup"
    INTERFACE_TIME = "interface_time"
    DISPENSING_TIME = "dispensing_time"
    ORDER_LIST_NAME = "order_list_name"
    ORDER_AMOUNT = "order_amount"
    BATCH_NAME = "batch_name"


class ConfigurationSortField(str, Enum):
    NAME = "name"
    SOLVER_TYPE = "solver_type"
    MOVER_AMOUNT = "mover_amount"
    TIME_LIMIT = "time_limit"
    PROCESS_AMOUNT = "process_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    BATCH_SIZE = "batch_size"
    WARMUP = "warmup"
    INTERFACE_TIME = "interface_time"
    DISPENSING_TIME = "dispensing_time"
    DISPENSE_RATE = "dispense_rate"
    VISCOSITY_EXPONENT = "viscosity_exponent"
    MOVER_SPEED = "mover_speed"
    MIXER_PRIMARY_TIME = "mixer_primary_time"
    MIXER_FINAL_TIME = "mixer_final_time"
    CAPPER_TIME = "capper_time"


class LayoutSortField(str, Enum):
    NAME = "name"
    TYPE = "type"
    INGREDIENT_LIST_TYPE = "ingredient_list_type"
    TILE_AMOUNT = "tile_amount"
    INTERFACE_AMOUNT = "interface_amount"
    DISPENSER_AMOUNT = "dispenser_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class OrderListSortField(str, Enum):
    NAME = "name"
    TYPE = "type"
    ORDER_AMOUNT = "order_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class IngredientListSortField(str, Enum):
    NAME = "name"
    TYPE = "type"
    INGREDIENT_AMOUNT = "ingredient_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class BatchSortField(str, Enum):
    NAME = "name"
    TOTAL_EXPERIMENT_AMOUNT = "total_experiment_amount"
    QUEUED_EXPERIMENT_AMOUNT = "queued_experiment_amount"
    FINISHED_EXPERIMENT_AMOUNT = "finished_experiment_amount"
    RUNNING_EXPERIMENT_AMOUNT = "running_experiment_amount"
    FAILED_EXPERIMENT_AMOUNT = "failed_experiment_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class OrderListType(str, Enum):
    MEDICINE = "medicine"
    PERFUME = "perfume"


class IngredientListType(str, Enum):
    MEDICINE = "medicine"
    PERFUME = "perfume"
