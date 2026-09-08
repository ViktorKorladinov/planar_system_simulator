import {useEffect, useMemo, useRef, useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {getLayout} from '../../api/layouts';
import type {LayoutSingleGetResponseDTO} from '../../types/layouts';
import {
    ArrowPathIcon,
    CircleStackIcon,
    DocumentDuplicateIcon,
    FunnelIcon,
    InformationCircleIcon,
    PlusCircleIcon,
    TruckIcon,
    XCircleIcon
} from '@heroicons/react/24/outline';
import IngredientListInfoModal from '../ingredient_lists/IngredientListInfoModal';

interface LayoutInfoModalProps {
    layoutId: number | null;
    onClose: () => void;
    onCopyCreate?: (data: LayoutSingleGetResponseDTO) => void;
}

// Helper to get formatted initials
const getDispenserInitials = (types: string[]) => {
    if (!types || !Array.isArray(types) || types.length === 0) return '';
    const result = [...types]
        .sort((a, b) => a.localeCompare(b))
        .slice(0, 5)
        .map(t => (typeof t === 'string' && t.length > 0) ? t.charAt(0).toUpperCase() : '')
        .filter(Boolean)
        .join(',')
    if (types.length > 5) return result + '...'
    return result
};

export default function LayoutInfoModal({layoutId, onClose, onCopyCreate}: LayoutInfoModalProps) {
    const gridContainerRef = useRef<HTMLDivElement>(null);

    const [zoom, setZoom] = useState(1);
    const [hoveredType, setHoveredType] = useState<string | null>(null);
    const [infoIngredientListId, setInfoIngredientListId] = useState<number | null>(null);

    // Fetch the specific layout
    const {data: layoutData, isLoading, isError} = useQuery({
        queryKey: ['layout', layoutId],
        queryFn: () => getLayout(layoutId!),
        enabled: !!layoutId,
    });

    // Derive dimensions and active ingredients strictly from fetched data
    const dimensions = useMemo(() => {
        if (!layoutData?.tiles || layoutData.tiles.length === 0) return {width: 3, height: 3};
        const maxX = Math.max(...layoutData.tiles.map(t => t.x)) + 1;
        const maxY = Math.max(...layoutData.tiles.map(t => t.y)) + 1;
        return {width: maxX, height: maxY};
    }, [layoutData]);

    const activeIngredients = useMemo(() => {
        if (!layoutData?.tiles) return [];
        const dt = new Set<string>();
        layoutData.tiles.forEach(t => t.dispensed_types?.forEach(d => dt.add(d)));
        return Array.from(dt).sort();
    }, [layoutData]);

    // Auto Zoom
    useEffect(() => {
        if (layoutData && gridContainerRef.current) {
            const padding = 32;
            const availableW = gridContainerRef.current.clientWidth - padding;
            const availableH = gridContainerRef.current.clientHeight - padding;
            const neededW = dimensions.width * 80 + Math.max(0, dimensions.width - 1) * 4;
            const neededH = dimensions.height * 80 + Math.max(0, dimensions.height - 1) * 4;

            if (neededW > 0 && neededH > 0) {
                const scaleW = availableW / neededW;
                const scaleH = availableH / neededH;
                const newZoom = Math.min(1, scaleW, scaleH);
                setZoom(Math.max(0.1, parseFloat(newZoom.toFixed(2))));
            }
        }
    }, [layoutData, dimensions]);

    if (!layoutId) return null;

    return (
        <div className="fixed inset-0 z-80 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col max-h-[95vh] h-225">

                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Layout Details</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100 transition-colors">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>

                <div className="flex-1 min-h-0 bg-gray-50 relative p-6">
                    {isLoading ? (
                        <div className="h-full flex items-center justify-center text-gray-500">Loading details...</div>
                    ) : isError || !layoutData ? (
                        <div className="h-full flex items-center justify-center text-red-500">Failed to load layout
                            details.</div>
                    ) : (
                        <div className="h-full flex gap-6">

                            {/* Left Side: General Info & Stats */}
                            <div className="w-56 flex flex-col gap-4 shrink-0 h-full">

                                {/* Info & Stats Block */}
                                <div
                                    className="bg-white border border-gray-200 rounded-md shadow-sm p-4 flex flex-col gap-4 shrink-0">
                                    <div>
                                        <label
                                            className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Name</label>
                                        <div className="text-sm font-medium text-gray-900">{layoutData.name ||
                                            <span className="text-gray-400 italic">Unnamed</span>}</div>
                                    </div>
                                    <div>
                                        <label
                                            className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Type</label>
                                        <div
                                            className="text-sm font-medium text-gray-800 capitalize">{layoutData.type.replace('_', ' ')}</div>
                                    </div>

                                    <div className="border-t border-gray-100 pt-3 mt-1">
                                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Layout
                                            Statistics</h3>
                                        <div className="grid grid-cols-2 gap-y-2 text-sm text-gray-600">
                                            <div className="flex items-center gap-1.5" title="Interface Tiles">
                                                <div className="text-blue-500"><TruckIcon className="w-4 h-4"/></div>
                                                <span className="font-medium">{layoutData.interface_amount}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5" title="Dispenser Tiles">
                                                <div className="text-orange-500"><FunnelIcon className="w-4 h-4"/></div>
                                                <span className="font-medium">{layoutData.dispenser_amount}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5" title="Mixer Tiles">
                                                <div className="text-green-500"><ArrowPathIcon className="w-4 h-4"/>
                                                </div>
                                                <span
                                                    className="font-medium">{layoutData.tiles.filter(t => t.type === 'mixer').length}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5" title="Capper Tiles">
                                                <div className="text-red-500"><CircleStackIcon className="w-4 h-4"/>
                                                </div>
                                                <span
                                                    className="font-medium">{layoutData.tiles.filter(t => t.type === 'capper').length}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5" title="Empty Tiles">
                                                <div className="text-gray-400"><PlusCircleIcon className="w-4 h-4"/>
                                                </div>
                                                <span
                                                    className="font-medium">{layoutData.tiles.filter(t => t.type === 'empty').length}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5" title="Blocked Tiles">
                                                <div className="text-gray-800"><XCircleIcon className="w-4 h-4"/></div>
                                                <span
                                                    className="font-medium">{layoutData.tiles.filter(t => t.type === 'blocked').length}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Ingredient List Binding */}
                                <div
                                    className="flex flex-col flex-1 min-h-0 bg-white border border-gray-200 rounded-md shadow-sm overflow-hidden">
                                    <div
                                        className="p-3 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
                                        <span className="font-semibold text-sm text-gray-800">Ingredients</span>
                                        {layoutData.ingredient_list_id && (
                                            <button
                                                onClick={() => setInfoIngredientListId(layoutData.ingredient_list_id)}
                                                className="p-1 text-green-700 bg-green-50 hover:bg-green-100 border border-green-700 rounded transition-colors shadow-sm"
                                                title="View Ingredient List Details"
                                            >
                                                <InformationCircleIcon className="w-4 h-4"/>
                                            </button>
                                        )}
                                    </div>

                                    <div
                                        className="bg-white border-b border-gray-100 p-2 text-xs font-medium text-center text-gray-600 truncate">
                                        {layoutData.ingredient_list?.name || `Linked List #${layoutData.ingredient_list_id}` || 'No list attached'}
                                    </div>

                                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                                        {activeIngredients.map(t => (
                                            <div
                                                key={t}
                                                onMouseEnter={() => setHoveredType(t)}
                                                onMouseLeave={() => setHoveredType(null)}
                                                className="flex items-center justify-between p-2.5 bg-gray-50 border border-gray-200 rounded text-sm hover:bg-gray-100 transition-colors"
                                            >
                                                <span className="truncate flex-1 font-medium text-gray-700"
                                                      title={t}>{t}</span>
                                            </div>
                                        ))}
                                        {activeIngredients.length === 0 && (
                                            <p className="text-xs text-gray-400 text-center mt-4 p-2">No ingredients
                                                configured.</p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Middle Grid */}
                            <div
                                className="flex-1 flex flex-col bg-white border border-gray-200 rounded-md shadow-sm relative overflow-hidden">
                                <div
                                    className="absolute top-3 right-3 z-20 flex items-center bg-white border border-gray-200 rounded-md shadow-sm opacity-90 hover:opacity-100 transition-opacity">
                                    <button onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}
                                            className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-l-md">
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                  d="M20 12H4"/>
                                        </svg>
                                    </button>
                                    <span
                                        className="px-2 text-xs font-medium text-gray-600 border-x border-gray-200 w-12 text-center">{Math.round(zoom * 100)}%</span>
                                    <button onClick={() => setZoom(z => Math.min(2.5, z + 0.1))}
                                            className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-r-md">
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                  d="M12 4v16m8-8H4"/>
                                        </svg>
                                    </button>
                                </div>

                                <div ref={gridContainerRef}
                                     className="flex-1 overflow-auto p-4 flex bg-gray-50/50 relative">
                                    <div className="m-auto">
                                        <div className="grid gap-1 relative" style={{
                                            gridTemplateColumns: `repeat(${dimensions.width}, ${80 * zoom}px)`,
                                            gridTemplateRows: `repeat(${dimensions.height}, ${80 * zoom}px)`
                                        }}>
                                            {layoutData.tiles.map((tile) => {
                                                const isHighlighted = hoveredType && tile.type === 'dispenser' && tile.dispensed_types.includes(hoveredType);
                                                return (
                                                    <div
                                                        key={`${tile.x}-${tile.y}`}
                                                        className={`w-full h-full border flex flex-col items-center justify-center relative transition-colors
                                                            ${tile.type === 'empty' ? 'bg-white border-gray-300 text-gray-200' : ''}
                                                            ${tile.type === 'blocked' ? 'bg-gray-800 border-gray-900 text-white' : ''}
                                                            ${tile.type === 'interface' ? 'bg-blue-50 border-blue-300 text-blue-600 shadow-sm' : ''}
                                                            ${tile.type === 'mixer' ? 'bg-green-50 border-green-300 text-green-600 shadow-sm' : ''}
                                                            ${tile.type === 'capper' ? 'bg-red-50 border-red-300 text-red-600 shadow-sm' : ''}
                                                            ${tile.type === 'dispenser' ? (isHighlighted ? 'bg-green-100 border-green-500 text-green-700 shadow-md ring-2 ring-green-300' : 'bg-orange-50 border-orange-300 text-orange-600 shadow-sm') : ''}
                                                        `}
                                                        title={tile.type === 'dispenser' ? tile.dispensed_types.join('\n') : ''}
                                                    >
                                                        {tile.type === 'empty' &&
                                                            <PlusCircleIcon className="w-[45%] h-[45%]"/>}
                                                        {tile.type === 'blocked' &&
                                                            <XCircleIcon className="w-[45%] h-[45%]"/>}
                                                        {tile.type === 'interface' &&
                                                            <TruckIcon className="w-[45%] h-[45%]"/>}
                                                        {tile.type === 'mixer' &&
                                                            <ArrowPathIcon className="w-[45%] h-[45%]"/>}
                                                        {tile.type === 'capper' &&
                                                            <CircleStackIcon className="w-[45%] h-[45%]"/>}
                                                        {tile.type === 'dispenser' && (
                                                            <>
                                                                {(tile.dispensed_types?.length > 0) && (
                                                                    <div
                                                                        className="absolute left-0 right-0 z-10 flex justify-center pointer-events-none"
                                                                        style={{
                                                                            top: `${4 * zoom}px`,
                                                                            padding: `0 ${4 * zoom}px`
                                                                        }}
                                                                    >
                                                                        <span
                                                                            className="font-bold text-orange-800 bg-white/90 border border-orange-200 rounded shadow-sm truncate leading-none"
                                                                            style={{
                                                                                fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                                padding: `${zoom}px ${4 * zoom}px`,
                                                                                borderWidth: `${Math.max(1, zoom)}px`
                                                                            }}
                                                                        >
                                                                            {getDispenserInitials(tile.dispensed_types)}
                                                                        </span>
                                                                    </div>
                                                                )}

                                                                <FunnelIcon className="w-[45%] h-[45%] z-0"/>

                                                                <div
                                                                    className="absolute left-1/2 -translate-x-1/2 z-10 flex items-center justify-center pointer-events-none"
                                                                    style={{bottom: `${4 * zoom}px`}}
                                                                >
                                                                    <span
                                                                        className="font-bold text-orange-900 bg-orange-100 border border-orange-300 text-center rounded shadow-sm leading-none tracking-tighter"
                                                                        style={{
                                                                            fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                            padding: `${zoom}px`,
                                                                            minWidth: `${16 * zoom}px`,
                                                                            borderWidth: `${Math.max(1, zoom)}px`
                                                                        }}
                                                                    >
                                                                        {tile.dispensed_types?.length > 99 ? '99+' : (tile.dispensed_types?.length || 0)}
                                                                    </span>
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    )}

                    {/* Sub-Modal for checking the attached Ingredient List details */}
                    <IngredientListInfoModal
                        listId={infoIngredientListId}
                        onClose={() => setInfoIngredientListId(null)}
                    />

                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end shrink-0">
                    {layoutData && onCopyCreate && (
                        <button
                            onClick={() => onCopyCreate(layoutData)}
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