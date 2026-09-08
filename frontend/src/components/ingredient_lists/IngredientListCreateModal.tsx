import {type ChangeEvent, type SyntheticEvent, useRef, useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createIngredientList} from '../../api/ingredient_lists';
import type {
    IngredientListCreateRequestDTO,
    IngredientListSingleGetResponseDTO,
    IngredientListType,
    NoteType
} from '../../types/ingredient_lists';
import {formatName} from '../../utils/formatters';

interface IngredientListCreateModalProps {
    isOpen: boolean;
    initialData?: IngredientListSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

interface UIIngredient {
    id: string;
    name: string;
    note_type: NoteType | '';
    viscosity: number | '';
    volatility_rank: number | '';
}

interface ParsedJSONIngredient {
    name?: string;
    note_type?: string;
    viscosity?: number;
    volatility_rank?: number;
}

interface ParsedJSONIngredientList {
    name?: string;
    type?: string;
    ingredients?: ParsedJSONIngredient[];
}

const generateId = () => Math.random().toString(36).substring(2, 9);
const getInitialIngredientState = (): UIIngredient[] => [{
    id: generateId(),
    name: '',
    note_type: '',
    viscosity: '',
    volatility_rank: ''
}];

export default function IngredientListCreateModal({
                                                      isOpen,
                                                      initialData,
                                                      onClose,
                                                      onSuccessSubmit
                                                  }: IngredientListCreateModalProps) {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    const [name, setName] = useState('');
    const [type, setType] = useState<IngredientListType>('medicine');
    const [ingredients, setIngredients] = useState<UIIngredient[]>(getInitialIngredientState);
    const [lastCopiedId, setLastCopiedId] = useState<number | null>(null);

    if (initialData && initialData.id !== lastCopiedId) {
        setLastCopiedId(initialData.id);
        setName(initialData.name ? `${initialData.name} (Copy)` : 'Copy');
        setType(initialData.type);

        if (initialData.ingredients && initialData.ingredients.length > 0) {
            setIngredients(initialData.ingredients.map(i => ({
                id: generateId(),
                name: i.name || '',
                note_type: i.note_type ?? '',
                viscosity: i.viscosity ?? '',
                volatility_rank: i.volatility_rank ?? ''
            })));
        } else {
            setIngredients(getInitialIngredientState());
        }
    }

    const resetState = () => {
        setName('');
        setType('medicine');
        setIngredients(getInitialIngredientState());
        setValidationErrors([]);
        setLastCopiedId(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const mutation = useMutation({
        mutationFn: async (data: IngredientListCreateRequestDTO) => {
            setValidationErrors([]);
            await createIngredientList(data, true);
            return await createIngredientList(data, false);
        },
        onSuccess: async (createdData) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['ingredient_list']}),
                queryClient.invalidateQueries({queryKey: ['ingredient_lists']}),
                queryClient.invalidateQueries({queryKey: ['ingredient_list_details']}),
                queryClient.invalidateQueries({queryKey: ['ingredient_lists_select']}),
                queryClient.invalidateQueries({queryKey: ['layout']}),
                queryClient.invalidateQueries({queryKey: ['layouts']}),
                queryClient.invalidateQueries({queryKey: ['layouts_select']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']}),
                queryClient.invalidateQueries({queryKey: ['batches']})
            ]);
            onSuccessSubmit(formatName(createdData.name), createdData.id);
            resetState();
            onClose();
        },
        onError: (errors: unknown) => {
            if (Array.isArray(errors)) setValidationErrors(errors);
            else if (typeof errors === 'string') setValidationErrors([errors]);
            else setValidationErrors(["An unexpected error occurred while saving."]);
        }
    });

    const handleDiscard = () => {
        if (window.confirm("Are you sure you want to discard your changes? This will reset the entire form.")) {
            resetState();
            onClose();
        }
    };

    const handleAddIngredient = () => setIngredients(prev => [...prev, {
        id: generateId(),
        name: '',
        note_type: 'base_note',
        viscosity: '',
        volatility_rank: ''
    }]);
    const handleRemoveIngredient = (id: string) => setIngredients(prev => prev.filter(ing => ing.id !== id));
    const handleIngredientChange = (id: string, field: keyof UIIngredient, value: string | number) => {
        setIngredients(prev => prev.map(ing => ing.id === id ? {...ing, [field]: value} : ing));
    };

    const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const json = JSON.parse(event.target?.result as string) as ParsedJSONIngredientList;

                if (!json.ingredients || !Array.isArray(json.ingredients)) {
                    setValidationErrors(["Invalid file format. 'ingredients' array is missing."]);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                    return;
                }

                if (json.name) setName(json.name);
                if (json.type && (json.type === 'medicine' || json.type === 'perfume')) setType(json.type as IngredientListType);

                const newIngredients: UIIngredient[] = json.ingredients.map((i) => ({
                    id: generateId(),
                    name: i.name || '',
                    note_type: (i.note_type as NoteType) || '',
                    viscosity: typeof i.viscosity === 'number' ? i.viscosity : '',
                    volatility_rank: typeof i.volatility_rank === 'number' ? i.volatility_rank : ''
                }));

                if (newIngredients.length === 0) newIngredients.push({
                    id: generateId(),
                    name: '',
                    note_type: '',
                    viscosity: '',
                    volatility_rank: ''
                });

                setIngredients(newIngredients);
                setValidationErrors([]);
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'Invalid JSON';
                setValidationErrors([`Failed to parse file: ${errorMessage}`]);
            }
            if (fileInputRef.current) fileInputRef.current.value = '';
        };
        reader.readAsText(file);
    };

    const handleSubmit = (e: SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault();
        const finalName = name.trim();

        const payload: IngredientListCreateRequestDTO = {
            name: finalName.length >= 1 ? finalName : null,
            type: type,
            ingredients: ingredients.map(i => ({
                name: i.name.trim(),
                note_type: type === 'perfume' ? (i.note_type as NoteType || 'base_note') : null,
                viscosity: type === 'perfume' ? Number(i.viscosity) : null,
                volatility_rank: type === 'perfume' ? Number(i.volatility_rank) : null
            }))
        };

        mutation.mutate(payload);
    };

    // Duplicate Detection Logic
    const duplicateIds = new Set<string>();
    const nameCounts = new Map<string, string[]>();

    ingredients.forEach(ing => {
        const normalizedName = ing.name.trim().toLowerCase();
        if (normalizedName) {
            if (!nameCounts.has(normalizedName)) {
                nameCounts.set(normalizedName, []);
            }
            nameCounts.get(normalizedName)!.push(ing.id);
        }
    });

    nameCounts.forEach(ids => {
        if (ids.length > 1) {
            ids.forEach(id => duplicateIds.add(id));
        }
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" onClick={onClose}></div>
            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-3xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Create Ingredient List</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>

                {validationErrors.length > 0 && (
                    <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md relative shrink-0">
                        <button onClick={() => setValidationErrors([])}
                                className="absolute top-2 right-2 text-red-400 hover:text-red-600">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                        <h4 className="text-sm font-semibold text-red-800 mb-1">Validation Errors:</h4>
                        <ul className="text-sm text-red-700 list-disc pl-5 max-h-24 overflow-y-auto">
                            {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0" autoComplete="off">
                    <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50 space-y-6">

                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input type="text" name="name" value={name} onChange={(e) => setName(e.target.value)}
                                       className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"
                                       placeholder="Enter list name... (Optional)" autoComplete="none"/>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                <select value={type} onChange={(e) => setType(e.target.value as IngredientListType)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 bg-white text-sm">
                                    <option value="medicine">Medicine</option>
                                    <option value="perfume">Perfume</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Ingredients</h3>
                            {ingredients.map((ing, index) => (
                                <div key={ing.id}
                                     className="relative bg-white p-4 rounded-md border border-gray-200 shadow-sm">

                                    {/* Delete Button (Only if more than 1 ingredient exists) */}
                                    {ingredients.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveIngredient(ing.id)}
                                            className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                                            title="Remove Ingredient"
                                        >
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
                                                 stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                      d="M6 18L18 6M6 6l12 12"/>
                                            </svg>
                                        </button>
                                    )}

                                    <h4 className="text-sm font-medium text-gray-800 mb-3">Ingredient {index + 1}</h4>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div
                                            className={type === 'medicine' ? "col-span-2" : "col-span-2 sm:col-span-1"}>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                                            <input
                                                required
                                                type="text"
                                                value={ing.name}
                                                onChange={(e) => handleIngredientChange(ing.id, 'name', e.target.value)}
                                                className={`w-full px-3 py-2 border rounded-md text-sm transition-colors ${
                                                    duplicateIds.has(ing.id)
                                                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500 bg-red-50'
                                                        : 'border-gray-300 focus:ring-gray-500 focus:border-gray-500'
                                                }`}
                                                placeholder="e.g. Alcohol"
                                            />
                                            {duplicateIds.has(ing.id) && (
                                                <p className="text-red-500 text-xs mt-1 font-medium">Name must be
                                                    unique.</p>
                                            )}
                                        </div>

                                        {type === 'perfume' && (
                                            <>
                                                <div className="col-span-2 sm:col-span-1">
                                                    <label className="block text-xs font-medium text-gray-500 mb-1">Note
                                                        Type</label>
                                                    <select required={type === 'perfume'} value={ing.note_type}
                                                            onChange={(e) => handleIngredientChange(ing.id, 'note_type', e.target.value)}
                                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 bg-white text-sm">
                                                        <option value="" disabled>Select...</option>
                                                        <option value="base_note">Base Note</option>
                                                        <option value="heart_note">Heart Note</option>
                                                        <option value="top_note">Top Note</option>
                                                        <option value="primary_solvent">Primary Solvent</option>
                                                        <option value="secondary_solvent">Secondary Solvent</option>
                                                    </select>
                                                </div>
                                                <div className="col-span-2 sm:col-span-1">
                                                    <label className="block text-xs font-medium text-gray-500 mb-1">Viscosity
                                                        (Float)</label>
                                                    <input required={type === 'perfume'} type="number" step="any"
                                                           min="0" value={ing.viscosity}
                                                           onChange={(e) => handleIngredientChange(ing.id, 'viscosity', e.target.value === '' ? '' : Number(e.target.value))}
                                                           className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"/>
                                                </div>
                                                <div className="col-span-2 sm:col-span-1">
                                                    <label className="block text-xs font-medium text-gray-500 mb-1">Volatility
                                                        Rank (Int)</label>
                                                    <input required={type === 'perfume'} type="number" step="1" min="0"
                                                           value={ing.volatility_rank}
                                                           onChange={(e) => handleIngredientChange(ing.id, 'volatility_rank', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                                                           className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"/>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}

                            <button type="button" onClick={handleAddIngredient}
                                    className="w-full py-3 border-2 border-dashed border-gray-300 rounded-md text-gray-600 font-medium hover:bg-gray-50 hover:border-gray-400 transition-colors flex items-center justify-center gap-2">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                                </svg>
                                Add Ingredient
                            </button>
                        </div>
                    </div>

                    <div
                        className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-between items-center shrink-0">
                        <div>
                            <input type="file" accept=".json" ref={fileInputRef} onChange={handleFileUpload}
                                   className="hidden" id="ingredient-file-upload"/>
                            <label htmlFor="ingredient-file-upload"
                                   className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 inline-flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                                </svg>
                                Load from File</label>
                        </div>

                        <div className="flex space-x-3">
                            <button type="button" onClick={handleDiscard}
                                    className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 hover:border-red-300 transition-colors">Discard
                            </button>
                            <button
                                type="submit"
                                disabled={mutation.isPending || duplicateIds.size > 0}
                                className="px-4 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center"
                            >
                                {mutation.isPending ? 'Validating...' : 'Create Ingredient List'}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}