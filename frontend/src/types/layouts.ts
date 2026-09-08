import type {IngredientListDTO, IngredientListType} from "./ingredient_lists.ts";

export type LayoutType = 'square' | 'line' | 'double_line' | 'ring' | 'custom'
export type TileType = 'interface' | 'blocked' | 'empty' | 'dispenser' | 'mixer' | 'capper'
export type LayoutSortField = 'name' | 'type' | 'tile_amount' | 'interface_amount' |
    'dispenser_amount' | 'created_at' | 'updated_at' | 'ingredient_list_type'

export interface TileDTO {
    type: TileType;
    dispensed_types: string[];
    x: number;
    y: number;
}

export interface LayoutDTO {
    name: string;
    type: LayoutType;
    tiles: TileDTO[];
    ingredient_list_id: number | null;
    ingredient_list: IngredientListDTO | null;
}

export interface LayoutDTO {
    name: string;
    type: LayoutType;
    tiles: TileDTO[];
}

export type LayoutSingleCreateRequestDTO = LayoutDTO

export interface LayoutSingleUpdateRequestDTO {
    name: string;
}

export interface LayoutSummaryResponseDTO {
    id: number;
    name: string;
    type: LayoutType;
    ingredient_list_type: IngredientListType;
    tile_amount: number;
    interface_amount: number;
    dispenser_amount: number;
    created_at: string;
    updated_at: string;
}

export interface LayoutBatchGetResponseDTO {
    total: number;
    page: number;
    size: number;
    layouts: LayoutSummaryResponseDTO[];
}

export interface LayoutSingleCreateResponseDTO extends LayoutSummaryResponseDTO {
    tiles: TileDTO[];
    is_dry_run: boolean;
    errors: string[];
}

export interface LayoutSingleGetResponseDTO {
    id: number;
    name: string;
    type: LayoutType;
    tiles: TileDTO[];
    ingredient_list_id: number | null;
    ingredient_list: IngredientListDTO;
    tile_amount: number;
    interface_amount: number;
    dispenser_amount: number;
    created_at: string;
    updated_at: string;
}