import type {SortDirection} from "../types/common.ts";
import type {
    LayoutBatchGetResponseDTO,
    LayoutSingleCreateRequestDTO,
    LayoutSingleCreateResponseDTO,
    LayoutSingleGetResponseDTO,
    LayoutSingleUpdateRequestDTO,
    LayoutSortField
} from "../types/layouts.ts";
import {createEntity} from "./base.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getLayouts(
    page: number,
    size: number,
    sortBy: LayoutSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
    layoutTypes?: string[]
): Promise<LayoutBatchGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) {
        params.append('search', search);
    }

    if (layoutTypes && layoutTypes.length > 0) {
        layoutTypes.forEach(type => params.append('layout_types', type));
    }

    const response = await fetch(`${API_BASE_URL}/layouts/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch layouts');
    }

    return response.json();
}

export async function createLayout(
    data: LayoutSingleCreateRequestDTO,
    isDryRun: boolean = false
): Promise<LayoutSingleCreateResponseDTO> {

    return createEntity<LayoutSingleCreateRequestDTO, LayoutSingleCreateResponseDTO>(
        'layouts',
        data,
        isDryRun
    );
}

export async function getLayout(id: number): Promise<LayoutSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/layouts/${id}`);
    if (!response.ok) throw new Error('Failed to fetch layout details');
    return response.json();
}

export async function updateLayout(id: number, data: LayoutSingleUpdateRequestDTO): Promise<LayoutSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/layouts/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update layouts"];
    }
    return response.json();
}

export async function deleteLayout(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/layouts/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete layout');
}