import type {ExperimentCreateRequestDTO, ExperimentSummaryResponseDTO} from "./experiments.ts";
import type {LayoutDTO} from "./layouts.ts";
import type {ConfigurationDTO} from "./configurations.ts";
import type {OrderListDTO} from "./order_lists.ts";

export type BatchSortField = 'name' | 'total_experiment_amount' | 'queued_experiment_amount' |
    'finished_experiment_amount' | 'running_experiment_amount' | 'failed_experiment_amount' |
    'created_at' | 'updated_at'

export interface ExperimentBatchCreateRequestDTO {
    name: string;
    experiments: ExperimentCreateRequestDTO[];
}

export interface ExperimentBatchSingleUpdateRequestDTO {
    name: string;
}

export interface ExperimentMatrixCreateRequestDTO {
    name: string;
    layout_ids: number[];
    layouts: LayoutDTO[];
    configuration_ids: number[];
    configurations: ConfigurationDTO[];
    order_list_ids: number[];
    order_lists: OrderListDTO[];
}

export interface BatchSummaryResponseDTO {
    id: number;
    name: string;
    total_experiment_amount: number;
    queued_experiment_amount: number;
    finished_experiment_amount: number;
    running_experiment_amount: number;
    failed_experiment_amount: number;
    created_at: string;
    updated_at: string;
}

export interface ExperimentBatchGetResponseDTO extends BatchSummaryResponseDTO {
    experiments: ExperimentSummaryResponseDTO[];
}

export interface ExperimentBatchCreateResponseDTO extends ExperimentBatchGetResponseDTO {
    created_amount: number;
    skipped_amount: number;
    estimated_time: number;
    is_dry_run: boolean;
    errors: string[];
}

export interface ExperimentBatchPaginatedGetResponseDTO {
    total: number;
    page: number;
    size: number;
    batches: BatchSummaryResponseDTO[];
}