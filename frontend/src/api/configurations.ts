import type {
    ConfigurationBatchGetResponseDTO,
    ConfigurationSingleCreateRequestDTO,
    ConfigurationSingleCreateResponseDTO,
    ConfigurationSingleGetResponseDTO,
    ConfigurationSingleUpdateRequestDTO,
    ConfigurationSortField
} from '../types/configurations';
import type {SortDirection} from "../types/common.ts";
import {createEntity} from "./base.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getConfigurations(
    page: number,
    size: number,
    sortBy: ConfigurationSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
    solverTypes?: string[]
): Promise<ConfigurationBatchGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) {
        params.append('search', search);
    }

    if (solverTypes && solverTypes.length > 0) {
        solverTypes.forEach(type => params.append('solver_types', type));
    }

    const response = await fetch(`${API_BASE_URL}/configurations/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch configurations');
    }

    return response.json();
}

export async function createConfiguration(
    data: ConfigurationSingleCreateRequestDTO,
    isDryRun: boolean = false
): Promise<ConfigurationSingleCreateResponseDTO> {

    return createEntity<ConfigurationSingleCreateRequestDTO, ConfigurationSingleCreateResponseDTO>(
        'configurations',
        data,
        isDryRun
    );
}

export async function getConfiguration(id: number): Promise<ConfigurationSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/configurations/${id}`);
    if (!response.ok) throw new Error('Failed to fetch configuration details');
    return response.json();
}

export async function updateConfiguration(id: number, data: ConfigurationSingleUpdateRequestDTO): Promise<ConfigurationSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/configurations/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update configuration"];
    }
    return response.json();
}

export async function deleteConfiguration(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/configurations/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete configuration');
}