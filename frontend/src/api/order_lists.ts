import type {SortDirection} from "../types/common.ts";
import type {
    OrderListBatchGetResponseDTO,
    OrderListCreateRequestDTO,
    OrderListSingleCreateResponseDTO,
    OrderListSingleGetResponseDTO,
    OrderListSingleUpdateRequestDTO,
    OrderListSortField
} from "../types/order_lists.ts";
import {createEntity} from "./base.ts";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

export async function getOrderLists(
    page: number,
    size: number,
    sortBy: OrderListSortField = 'created_at',
    sortDir: SortDirection = 'desc',
    search?: string,
    orderListTypes?: string[]
): Promise<OrderListBatchGetResponseDTO> {

    const params = new URLSearchParams({
        page: page.toString(),
        size: size.toString(),
        sort_by: sortBy,
        sort_dir: sortDir,
    });

    if (search) {
        params.append('search', search);
    }
    if (orderListTypes && orderListTypes.length > 0) {
        orderListTypes.forEach(type => params.append('types', type));
    }


    const response = await fetch(`${API_BASE_URL}/order_lists/?${params.toString()}`);

    if (!response.ok) {
        throw new Error('Failed to fetch order lists');
    }

    return response.json();
}

export async function createOrderList(
    data: OrderListCreateRequestDTO,
    isDryRun: boolean = false
): Promise<OrderListSingleCreateResponseDTO> {

    return createEntity<OrderListCreateRequestDTO, OrderListSingleCreateResponseDTO>(
        'order_lists',
        data,
        isDryRun
    );
}

export async function getOrderList(id: number): Promise<OrderListSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/order_lists/${id}`);
    if (!response.ok) throw new Error('Failed to fetch order list details');
    return response.json();
}

export async function updateOrderList(id: number, data: OrderListSingleUpdateRequestDTO): Promise<OrderListSingleGetResponseDTO> {
    const response = await fetch(`${API_BASE_URL}/order_lists/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw errData.detail || ["Failed to update order list"];
    }
    return response.json();
}

export async function deleteOrderList(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/order_lists/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete order list');
}