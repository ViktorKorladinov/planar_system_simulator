import type {PydanticValidationError} from "../types/common.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function createEntity<TRequest, TResponse>(
    endpoint: string,
    data: TRequest,
    isDryRun: boolean = false
): Promise<TResponse> {
    const url = new URL(`${API_BASE_URL}/${endpoint}/`);

    if (isDryRun) {
        url.searchParams.append('dry_run', 'true');
    }

    const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        if (response.status === 422) {
            if (errorData.detail && Array.isArray(errorData.detail)) {
                throw errorData.detail.map((err: PydanticValidationError) => {
                    const fieldName = err.loc[err.loc.length - 1];
                    return `Field '${fieldName}': ${err.msg}`;
                });
            }

            if (errorData.errors && Array.isArray(errorData.errors)) {
                throw errorData.errors;
            }
        }

        throw ["An unexpected server error occurred."];
    }

    return response.json();
}