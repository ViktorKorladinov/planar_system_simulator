import {createEntity} from "./base.ts";
import type {SortDirection} from "../types/common.ts";
import type {
    IngredientListBatchGetResponseDTO,
    IngredientListCreateRequestDTO,
    IngredientListSingleCreateResponseDTO,
    IngredientListSingleGetResponseDTO,
    IngredientListSingleUpdateRequestDTO,
    IngredientListSortField
} from "../types/ingredient_lists.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getIngredientLists(
    page: number,
    size: number,
    sortBy: IngredientListSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
    ingredientListTypes?: string[]
): Promise<IngredientListBatchGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) {
        params.append('search', search);
    }
    if (ingredientListTypes && ingredientListTypes.length > 0) {
        ingredientListTypes.forEach(type => params.append('types', type));
    }


    const response = await fetch(`${API_BASE_URL}/ingredient_lists/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch ingredient lists');
    }

    return response.json();
}

export async function createIngredientList(
    data: IngredientListCreateRequestDTO,
    isDryRun: boolean = false
): Promise<IngredientListSingleCreateResponseDTO> {

    return createEntity<IngredientListCreateRequestDTO, IngredientListSingleCreateResponseDTO>(
        'ingredient_lists',
        data,
        isDryRun
    );
}

export async function getIngredientList(id: number): Promise<IngredientListSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/ingredient_lists/${id}`);
    if (!response.ok) throw new Error('Failed to fetch ingredient list details');
    return response.json();
}

export async function updateIngredientList(id: number, data: IngredientListSingleUpdateRequestDTO): Promise<IngredientListSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/ingredient_lists/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update ingredient list"];
    }
    return response.json();
}

export async function deleteIngredientList(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/ingredient_lists/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete ingredient list');
}