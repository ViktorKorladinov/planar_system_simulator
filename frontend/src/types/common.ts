export type SortDirection = 'asc' | 'desc';

export interface PydanticValidationError {
    loc: (string | number)[];
    msg: string;
    type: string;
}

export interface ToastMessage {
    id: string;
    message: string;
    type: 'success' | 'error';
    actionId?: number;
}