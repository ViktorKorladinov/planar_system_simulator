import {useQuery} from '@tanstack/react-query';
import {getIngredientList} from '../../api/ingredient_lists';
import type {IngredientListSingleGetResponseDTO} from '../../types/ingredient_lists';
import {DocumentDuplicateIcon} from '@heroicons/react/24/outline';

interface IngredientListInfoModalProps {
    listId: number | null;
    onClose: () => void;
    onCopyCreate?: (data: IngredientListSingleGetResponseDTO) => void;
}

export default function IngredientListInfoModal({listId, onClose, onCopyCreate}: IngredientListInfoModalProps) {
    const {data, isLoading, isError} = useQuery({
        queryKey: ['ingredient_list', listId],
        queryFn: () => getIngredientList(listId!),
        enabled: !!listId,
    });

    if (!listId) return null;

    return (
        <div className="fixed inset-0 z-80 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Ingredient List Details</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>

                <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50">
                    {isLoading ? (
                        <p className="text-gray-500 text-center py-10">Loading details...</p>
                    ) : isError ? (
                        <p className="text-red-500 text-center py-10">Failed to load data.</p>
                    ) : (
                        <div className="space-y-6">
                            <div
                                className="bg-white p-4 rounded-md border border-gray-200 shadow-sm grid grid-cols-1 gap-3">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <div
                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center">
                                    {data?.name || <span className="text-gray-400 italic">No name provided</span>}
                                </div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                <div
                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center capitalize">
                                    {data?.type || <span className="text-gray-400 italic">No type provided</span>}
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Ingredients</h3>
                                {data?.ingredients?.map((ing, index) => (
                                    <div key={index}
                                         className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                        <h4 className="text-sm font-medium text-gray-800 mb-3">Ingredient {index + 1}</h4>

                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div
                                                className={data.type === 'medicine' ? "col-span-2" : "col-span-2 sm:col-span-1"}>
                                                <label
                                                    className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{ing.name}</div>
                                            </div>

                                            {data.type === 'perfume' && (
                                                <>
                                                    <div className="col-span-2 sm:col-span-1">
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">Note
                                                            Type</label>
                                                        <div
                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center capitalize">
                                                            {ing.note_type ? ing.note_type.replace('_', ' ') :
                                                                <span className="text-gray-400 italic">Not set</span>}
                                                        </div>
                                                    </div>
                                                    <div className="col-span-2 sm:col-span-1">
                                                        <label
                                                            className="block text-xs font-medium text-gray-500 mb-1">Viscosity</label>
                                                        <div
                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                            {ing.viscosity ??
                                                                <span className="text-gray-400 italic">Not set</span>}
                                                        </div>
                                                    </div>
                                                    <div className="col-span-2 sm:col-span-1">
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">Volatility
                                                            Rank</label>
                                                        <div
                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                            {ing.volatility_rank ??
                                                                <span className="text-gray-400 italic">Not set</span>}
                                                        </div>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {(!data?.ingredients || data.ingredients.length === 0) && (
                                    <p className="text-gray-500 text-center py-4">No ingredients found.</p>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end shrink-0">
                    {data && onCopyCreate && (
                        <button
                            onClick={() => onCopyCreate(data)}
                            className="px-4 py-2 text-sm font-medium text-white bg-gray-900 border border-transparent rounded-md hover:bg-black shadow-sm flex items-center gap-2"
                        >
                            <DocumentDuplicateIcon className="w-4 h-4"/>
                            Copy & Create
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}