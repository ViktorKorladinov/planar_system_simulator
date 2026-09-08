export type OrderListSortField = 'name' | 'order_amount' | 'created_at' | 'updated_at' | 'type';
export type OrderListType = 'medicine' | 'perfume'

export interface OrderItemDTO {
    name: string;
    quantity: number;
}

export interface OrderDTO {
    items: OrderItemDTO[];
    t_max: number | null;
}

export interface OrderListDTO {
    name: string | null;
    type: OrderListType;
    orders: OrderDTO[];
}

export type OrderListCreateRequestDTO = OrderListDTO

export interface OrderListSingleUpdateRequestDTO {
    name: string;
}

export interface OrderListSingleGetResponseDTO extends OrderListDTO {
    id: number;
    name: string;
    type: OrderListType;
    order_amount: number;
    created_at: string;
    updated_at: string;
}

export interface OrderListShortResponseDTO {
    id: number;
    name: string;
    type: OrderListType;
    order_amount: number;
    created_at: string;
    updated_at: string;
}

export interface OrderListBatchGetResponseDTO {
    total: number;
    page: number;
    size: number;
    order_lists: OrderListShortResponseDTO[];
}

export interface OrderListSingleCreateResponseDTO {
    id: number;
    name: string;
    type: OrderListType;
    orders: OrderListDTO[];
    order_amount: number;
    created_at: string;
    updated_at: string;
    is_dry_run: boolean;
    errors: string[];
}