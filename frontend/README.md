# Xplanar Experiment Configurator Frontend

This projects includes frontend implementation for Xplanar Experiment Configurator.

## Contacts
**Author:** Vojtěch Mička  
**Email:** mickavo2@student.cvut.cz

## Content

This repository contains the following directories inside `src` directory:
- `api` - directory related to the functions used for communication with the REST API
- `components` - directory with components for user interface
- `hooks` - directory with hook for page resizing
- `pages` - directory with views
- `types` - directory with data types mostly matching DTOs from backend
- `utils` - directory with functions for data formating

## Configuration

- It's possible to configure URLs for frontend and simulator via the following environment variables. (Prefix VITE is necessary due to Vite usage.)
- `VITE_BACKEND_URL` - URL for backend REST API (default value: http://localhost:800/api/v1)
- `VITE_SIMULATOR_URL` - URL for simulator which is needed to display simulations (default value: http://localhost:3000)

## Dependencies

- To run this project locally, you need to have [Node.js](https://nodejs.org/) installed.
- Dependencies can be installed with the following command: ```npm install```

## How to Run

1. Use the following command to start the development server: ```npm run dev```
2. Open [http://localhost:5173/](http://localhost:5173/) in your browser.

## Supported File Formats

- JSON files used to import order list or ingredient list should have the following formats.

### File with Order List (Medicine)

```ts
interface OrderItem {
    name: string;
}

interface Order {
    items: OrderItem[];
}

interface OrderList {
    name: string | null;
    type: 'medicine';
    orders: Order[];
}
```

### File with Order List (Perfumes)

```ts
interface OrderItem {
    name: string;
    quantity: number;
}

interface Order {
    items: OrderItem[];
    t_max: number;
}

interface OrderList {
    name: string | null;
    type: 'perfume';
    orders: Order[];
}
```

### File with Ingredient List (Medicine)

```ts
interface Ingredient {
    name: string;
}

interface IngredientList {
    name: string | null;
    type: 'medicine';
    ingredients: Ingredient[];
}
```

### File with Ingredient List (Perfume)

```ts
type NoteType = 'base_note' | 'heart_note' | 'top_note' | 'primary_solvent' | 'secondary_solvent'

interface Ingredient {
    name: string;
    note_type: NoteType
    viscosity: number;
    volatility_rank: number;
}

interface IngredientList {
    name: string | null;
    type: 'perfume';
    ingredients: Ingredient[];
}
```

## License

[MIT license](LICENSE)