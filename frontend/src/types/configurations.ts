export type SolverType = 'cplex_medicine' | 'cplex_perfumes' | 'hexaly';
export type ConfigurationSortField = 'name' | 'solver_type' | 'mover_amount' |
    'time_limit' | 'process_amount' | 'created_at' | 'updated_at' | 'batch_size' |
    'warmup' | 'interface_time' | 'dispensing_time' | 'dispense_rate' | 'viscosity_exponent' |
    'mover_speed' | 'mixer_primary_time' | 'mixer_final_time' | 'capper_time';

export interface ConfigurationDTO {
    name: string | null;
    solver_type: string;
    interface_time: number;
    dispensing_time: number;
    mover_amount: number;
    time_limit: number;
    process_amount: number;
    batch_size: number | null;
    warmup: boolean | null;
    dispense_rate: number | null;
    viscosity_exponent: number | null;
    mover_speed: number | null;
    mixer_primary_time: number | null;
    mixer_final_time: number | null;
    capper_time: number | null;
}

export interface ConfigurationSummaryDTO {
    id: number;
    name: string;
    solver_type: SolverType;
    interface_time: number;
    dispensing_time: number;
    mover_amount: number;
    time_limit: number;
    process_amount: number;
    created_at: string;
    updated_at: string;
    batch_size: number | null;
    warmup: boolean | null;
    dispense_rate: number | null;
    viscosity_exponent: number | null;
    mover_speed: number | null;
    mixer_primary_time: number | null;
    mixer_final_time: number | null;
    capper_time: number | null;
}

export interface ConfigurationBatchGetResponseDTO {
    total: number;
    page: number;
    size: number;
    configurations: ConfigurationSummaryDTO[];
}

export type ConfigurationSingleCreateRequestDTO = ConfigurationDTO

export interface ConfigurationSingleCreateResponseDTO {
    id: number;
    errors: string[];
    is_dry_run: boolean;
    name: string;
}

export interface ConfigurationSingleUpdateRequestDTO {
    name: string;
}

export type ConfigurationSingleGetResponseDTO = ConfigurationSummaryDTO