export type IngredientListSortField = 'name' | 'ingredient_amount' | 'created_at' | 'updated_at' | 'type';
export type IngredientListType = 'medicine' | 'perfume'
export type NoteType = 'base_note' | 'heart_note' | 'top_note' | 'primary_solvent' | 'secondary_solvent'

export interface IngredientDTO {
    name: string;
    note_type: NoteType | null;
    viscosity: number | null;
    volatility_rank: number | null;
}

export interface IngredientListDTO {
    name: string | null;
    type: IngredientListType;
    ingredients: IngredientDTO[];
}

export type IngredientListCreateRequestDTO = IngredientListDTO

export interface IngredientListSingleUpdateRequestDTO {
    name: string;
}

export interface IngredientListSingleGetResponseDTO extends IngredientListDTO {
    id: number;
    name: string;
    type: IngredientListType;
    ingredient_amount: number;
    created_at: string;
    updated_at: string;
}

export interface IngredientListShortResponseDTO {
    id: number;
    name: string;
    type: IngredientListType;
    ingredient_amount: number;
    created_at: string;
    updated_at: string;
}

export interface IngredientListBatchGetResponseDTO {
    total: number;
    page: number;
    size: number;
    ingredient_lists: IngredientListShortResponseDTO[];
}

export interface IngredientListSingleCreateResponseDTO {
    id: number;
    name: string;
    type: IngredientListType;
    ingredients: IngredientListDTO[];
    ingredient_amount: number;
    created_at: string;
    updated_at: string;
    is_dry_run: boolean;
    errors: string[];
}