import {type SyntheticEvent, useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {createIngredientList} from '../../api/ingredient_lists';
import type {
    IngredientDTO,
    IngredientListCreateRequestDTO,
    IngredientListSingleGetResponseDTO,
    IngredientListType,
    NoteType
} from '../../types/ingredient_lists';

interface Props {
    isOpen: boolean;
    initialData?: IngredientListCreateRequestDTO | IngredientListSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessDraft: (payload: IngredientListCreateRequestDTO) => void;
}

interface UIIngredient {
    id: string;
    name: string;
    note_type: NoteType | '';
    viscosity: number | '';
    volatility_rank: number | '';
}

const generateId = () => Math.random().toString(36).substring(2, 9);
const getInitialIngredientState = (): UIIngredient[] => [{
    id: generateId(),
    name: '',
    note_type: '',
    viscosity: '',
    volatility_rank: ''
}];

export default function LayoutIngredientListDraftModal({isOpen, initialData, onClose, onSuccessDraft}: Props) {
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    const [name, setName] = useState('');
    const [type, setType] = useState<IngredientListType>('medicine');
    const [ingredients, setIngredients] = useState<UIIngredient[]>([]);

    const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
    const [prevInitialData, setPrevInitialData] = useState(initialData);

    if (isOpen !== prevIsOpen || initialData !== prevInitialData) {
        setPrevIsOpen(isOpen);
        setPrevInitialData(initialData);

        if (isOpen) {
            if (initialData) {
                setName(initialData.name || '');
                setType(initialData.type || 'medicine');
                if (initialData.ingredients && initialData.ingredients.length > 0) {
                    setIngredients(initialData.ingredients.map((i: IngredientDTO) => ({
                        id: generateId(),
                        name: i.name || '',
                        note_type: i.note_type ?? '',
                        viscosity: i.viscosity ?? '',
                        volatility_rank: i.volatility_rank ?? ''
                    })));
                } else {
                    setIngredients(getInitialIngredientState());
                }
            } else {
                setName('');
                setType('medicine');
                setIngredients(getInitialIngredientState());
            }
            setValidationErrors([]);
        }
    }

    const mutation = useMutation({
        mutationFn: async (data: IngredientListCreateRequestDTO) => {
            await createIngredientList(data, true);
            return data;
        },
        onSuccess: (validatedData) => {
            onSuccessDraft(validatedData);
        },
        onError: (errors: unknown) => {
            if (Array.isArray(errors)) setValidationErrors(errors);
            else if (typeof errors === 'string') setValidationErrors([errors]);
            else setValidationErrors(["Validation failed."]);
        }
    });

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

    const handleSubmit = (e: SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault();

        const seenNames = new Set<string>();
        const duplicates = new Set<string>();
        ingredients.forEach(ing => {
            const normalizedName = ing.name.trim().toLowerCase();
            if (normalizedName) {
                if (seenNames.has(normalizedName)) duplicates.add(ing.name.trim());
                else seenNames.add(normalizedName);
            }
        });

        if (duplicates.size > 0) {
            setValidationErrors([`Duplicate ingredients found: ${Array.from(duplicates).join(', ')}`]);
            return;
        }

        const payload: IngredientListCreateRequestDTO = {
            name: name.trim() || null,
            type,
            ingredients: ingredients.map(i => ({
                name: i.name.trim(),
                note_type: type === 'perfume' ? ((i.note_type as NoteType) || 'base_note') : null,
                viscosity: type === 'perfume' ? Number(i.viscosity) : null,
                volatility_rank: type === 'perfume' ? Number(i.volatility_rank) : null
            }))
        };

        mutation.mutate(payload);
    };

    // Calculate real-time inline highlighting for duplicate arrays
    const duplicateIds = new Set<string>();
    const nameCounts = new Map<string, string[]>();

    ingredients.forEach(ing => {
        const normalizedName = ing.name.trim().toLowerCase();
        if (normalizedName) {
            if (!nameCounts.has(normalizedName)) nameCounts.set(normalizedName, []);
            nameCounts.get(normalizedName)!.push(ing.id);
        }
    });

    nameCounts.forEach(ids => {
        if (ids.length > 1) ids.forEach(id => duplicateIds.add(id));
    });

    if (!isOpen) return null;

    return (
        <div
            className="absolute inset-0 z-60 flex items-center justify-center p-6 bg-black/20 backdrop-blur-[1px] rounded-lg">
            <div
                className="bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-3xl flex flex-col max-h-full">

                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Configure Ingredient List</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-md">✕</button>
                </div>

                {validationErrors.length > 0 && (
                    <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md relative shrink-0">
                        <button onClick={() => setValidationErrors([])}
                                className="absolute top-2 right-2 text-red-400 hover:text-red-600">✕
                        </button>
                        <ul className="text-sm text-red-700 list-disc pl-5">
                            {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
                    <div className="p-6 overflow-y-auto space-y-6">
                        <div className="p-3 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
                            <strong>Note:</strong> You are editing a draft list. It will not be permanently saved to
                            your database until you click "Create Layout".
                        </div>

                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                                       className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                                       placeholder="List name... (Optional)"/>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                <select value={type} onChange={(e) => setType(e.target.value as IngredientListType)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
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
                                    {ingredients.length > 1 && (
                                        <button type="button" onClick={() => handleRemoveIngredient(ing.id)}
                                                className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md">✕</button>
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
                                                className={`w-full px-3 py-2 border rounded-md text-sm ${duplicateIds.has(ing.id) ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
                                                placeholder="e.g. Alcohol"
                                            />
                                            {duplicateIds.has(ing.id) &&
                                                <p className="text-red-500 text-xs mt-1">Name must be unique.</p>}
                                        </div>

                                        {type === 'perfume' && (
                                            <>
                                                <div className="col-span-2 sm:col-span-1">
                                                    <label className="block text-xs font-medium text-gray-500 mb-1">Note
                                                        Type</label>
                                                    <select required value={ing.note_type}
                                                            onChange={(e) => handleIngredientChange(ing.id, 'note_type', e.target.value)}
                                                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
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
                                                    <input required type="number" step="any" min="0"
                                                           value={ing.viscosity}
                                                           onChange={(e) => handleIngredientChange(ing.id, 'viscosity', e.target.value === '' ? '' : Number(e.target.value))}
                                                           className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                                </div>
                                                <div className="col-span-2 sm:col-span-1">
                                                    <label className="block text-xs font-medium text-gray-500 mb-1">Volatility
                                                        Rank (Int)</label>
                                                    <input required type="number" step="1" min="0"
                                                           value={ing.volatility_rank}
                                                           onChange={(e) => handleIngredientChange(ing.id, 'volatility_rank', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                                                           className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}

                            <button type="button" onClick={handleAddIngredient}
                                    className="w-full py-3 border-2 border-dashed border-gray-300 rounded-md text-gray-600 font-medium hover:bg-gray-50">+
                                Add Ingredient
                            </button>
                        </div>
                    </div>

                    <div
                        className="px-6 py-4 border-t border-gray-200 bg-white flex justify-end gap-3 shrink-0 rounded-b-lg">
                        <button type="button" onClick={onClose}
                                className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">Cancel
                        </button>
                        <button type="submit" disabled={mutation.isPending || duplicateIds.size > 0}
                                className="px-4 py-2 text-sm text-white bg-black rounded-md hover:bg-black disabled:opacity-50">
                            {mutation.isPending ? 'Validating...' : 'Save Draft'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}