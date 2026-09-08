import type {SortDirection} from "../types/common.ts";
import type {
    BatchSortField,
    ExperimentBatchCreateRequestDTO,
    ExperimentBatchCreateResponseDTO,
    ExperimentBatchGetResponseDTO,
    ExperimentBatchPaginatedGetResponseDTO,
    ExperimentBatchSingleUpdateRequestDTO,
    ExperimentMatrixCreateRequestDTO
} from "../types/batches.ts";
import {createEntity} from "./base.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getBatches(
    page: number,
    size: number,
    sortBy: BatchSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
): Promise<ExperimentBatchPaginatedGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) {
        params.append('search', search);
    }

    const response = await fetch(`${API_BASE_URL}/experiments/batch/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch batch');
    }

    return response.json();
}

export async function createBatch(
    data: ExperimentBatchCreateRequestDTO,
    isDryRun: boolean = false
): Promise<ExperimentBatchCreateResponseDTO> {

    return createEntity<ExperimentBatchCreateRequestDTO, ExperimentBatchCreateResponseDTO>(
        'experiments/batch',
        data,
        isDryRun
    );
}

export async function createBatchMatrix(
    data: ExperimentMatrixCreateRequestDTO,
    isDryRun: boolean = false
): Promise<ExperimentBatchCreateResponseDTO> {

    return createEntity<ExperimentMatrixCreateRequestDTO, ExperimentBatchCreateResponseDTO>(
        'experiments/batch/matrix',
        data,
        isDryRun
    );
}

export async function getBatch(id: number): Promise<ExperimentBatchGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/experiments/batch/${id}`);
    if (!response.ok) throw new Error('Failed to fetch batch details');
    return response.json();
}

export async function updateBatch(id: number, data: ExperimentBatchSingleUpdateRequestDTO): Promise<ExperimentBatchGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/experiments/batch/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update batch"];
    }
    return response.json();
}

export async function deleteBatch(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/experiments/batch/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete batch');
}