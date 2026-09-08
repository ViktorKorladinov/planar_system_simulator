import type {SortDirection} from "../types/common.ts";
import type {
    ExperimentPaginatedGetResponseDTO,
    ExperimentSingleCreateRequestDTO,
    ExperimentSingleCreateResponseDTO,
    ExperimentSingleGetResponseDTO,
    ExperimentSingleUpdateRequestDTO,
    ExperimentSortField
} from "../types/experiments.ts";
import {createEntity} from "./base.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getExperiments(
    page: number,
    size: number,
    sortBy: ExperimentSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
    statuses?: string[],
    layoutTypes?: string[],
    solverTypes?: string[],
    batchId?: number
): Promise<ExperimentPaginatedGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) params.append('search', search);
    if (batchId) params.append('batch_id', batchId.toString());

    if (statuses && statuses.length > 0) {
        statuses.forEach(type => params.append('statuses', type));
    }

    if (layoutTypes && layoutTypes.length > 0) {
        layoutTypes.forEach(type => params.append('layout_types', type));
    }

    if (solverTypes && solverTypes.length > 0) {
        solverTypes.forEach(type => params.append('solver_types', type));
    }

    const response = await fetch(`${API_BASE_URL}/experiments/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch experiments');
    }

    return response.json();
}

export async function createExperiment(
    data: ExperimentSingleCreateRequestDTO,
    isDryRun: boolean = false
): Promise<ExperimentSingleCreateResponseDTO> {

    return createEntity<ExperimentSingleCreateRequestDTO, ExperimentSingleCreateResponseDTO>(
        'experiments',
        data,
        isDryRun
    );
}

export async function getExperiment(id: number): Promise<ExperimentSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/experiments/${id}`);
    if (!response.ok) throw new Error('Failed to fetch experiment details');
    return response.json();
}

export async function updateExperiment(id: number, data: ExperimentSingleUpdateRequestDTO): Promise<ExperimentSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/experiments/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update experiment"];
    }
    return response.json();
}

export async function deleteExperiment(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/experiments/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete experiment');
}