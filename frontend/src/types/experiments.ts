import type {LayoutDTO, LayoutType} from "./layouts.ts";
import type {ConfigurationDTO, SolverType} from "./configurations.ts";
import type {OrderListDTO} from "./order_lists.ts";
import type {IngredientListDTO} from "./ingredient_lists.ts";

export type ExperimentStatus = 'queued' | 'running' | 'finished' | 'failed';
export type ExperimentSortField = 'name' | 'status' | 'created_at' | 'updated_at' | 'started_at' |
    'finished_at' | 'tile_amount' | 'interface_amount' | 'dispenser_amount' | 'layout_type' |
    'layout_name' | 'configuration_name' | 'solver_type' | 'mover_amount' | 'time_limit' |
    'process_amount' | 'batch_size' | 'warmup' | 'interface_time' | 'dispensing_time' |
    'order_list_name' | 'order_amount'

export interface ExperimentCreateRequestDTO {
    name: string;
    layout_id: number;
    layout: LayoutDTO;
    configuration_id: number;
    configuration: ConfigurationDTO;
    order_list_id: number;
    order_list: OrderListDTO;
}

export type ExperimentSingleCreateRequestDTO = ExperimentCreateRequestDTO;

export interface ExperimentSingleUpdateRequestDTO {
    name: string;
}

export interface ExperimentFullResponseDTO {
    id: number;
    name: string;
    layout_id: number;
    layout: LayoutDTO;
    configuration_id: number;
    configuration: ConfigurationDTO;
    ingredient_list_id: number;
    ingredient_list: IngredientListDTO;
    order_list_id: number;
    order_list: OrderListDTO;
    batch_id: number;
    batch_name: string;
    status: ExperimentStatus;
    created_at: string;
    updated_at: string;
    started_at: string;
    finished_at: string;
}

export interface ExperimentSummaryResponseDTO {
    id: number;
    name: string;
    status: ExperimentStatus;
    created_at: string;
    updated_at: string;
    started_at: string;
    finished_at: string;
    batch_id: number;
    batch_name: string;
    tile_amount: number;
    interface_amount: number;
    dispenser_amount: number;
    layout_id: number;
    layout_type: LayoutType;
    layout_name: string;
    configuration_id: number;
    configuration_name: string;
    solver_type: SolverType;
    mover_amount: number;
    time_limit: number;
    batch_size: number;
    process_amount: number;
    order_list_id: number;
    order_list_name: string;
    order_amount: number;
    warmup: boolean;
    interface_time: number;
    dispensing_time: number;
}

export interface ExperimentPaginatedGetResponseDTO {
    total: number;
    page: number;
    size: number;
    experiments: ExperimentSummaryResponseDTO[];
}

export interface ExperimentSingleCreateResponseDTO extends ExperimentFullResponseDTO {
    is_dry_run: boolean;
    errors: string[];
}

export type ExperimentSingleGetResponseDTO = ExperimentSingleCreateResponseDTO;