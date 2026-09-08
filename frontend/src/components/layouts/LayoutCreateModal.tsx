import * as React from 'react';
import {type SyntheticEvent, useMemo, useRef, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {createLayout} from '../../api/layouts';
import {getIngredientList} from '../../api/ingredient_lists';
import type {
    LayoutSingleCreateRequestDTO,
    LayoutSingleGetResponseDTO,
    LayoutType,
    TileDTO,
    TileType
} from '../../types/layouts';
import type {IngredientListCreateRequestDTO} from '../../types/ingredient_lists';
import {formatName} from '../../utils/formatters';
import {
    ArrowPathIcon,
    CircleStackIcon,
    FunnelIcon,
    MagnifyingGlassIcon,
    PencilSquareIcon,
    PlusCircleIcon,
    TrashIcon,
    TruckIcon,
    XCircleIcon
} from '@heroicons/react/24/outline';
import IngredientListSelectModal from "../ingredient_lists/IngredientListSelectModal";
import LayoutIngredientListDraftModal from "./LayoutIngredientListDraftModal";
import IngredientListInfoModal from '../ingredient_lists/IngredientListInfoModal';

interface LayoutCreateModalProps {
    isOpen: boolean;
    initialData: LayoutSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

interface Dimensions {
    width: number;
    height: number;
}

// Helper to check if tile is edge
const isEdge = (x: number, y: number, w: number, h: number) => x === 0 || y === 0 || x === w - 1 || y === h - 1;

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

export default function LayoutCreateModal({isOpen, initialData, onClose, onSuccessSubmit}: LayoutCreateModalProps) {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const gridContainerRef = useRef<HTMLDivElement>(null);

    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    // Layout Form State
    const [name, setName] = useState('');
    const [layoutType, setLayoutType] = useState<LayoutType | null>(null);
    const [savedLayoutType, setSavedLayoutType] = useState<LayoutType | null>(null);
    const [dimensions, setDimensions] = useState<Dimensions>({width: 3, height: 3});
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [zoom, setZoom] = useState(1);

    // Grid / Editor State
    const [tiles, setTiles] = useState<TileDTO[]>([]);
    const [orphanDispensers, setOrphanDispensers] = useState<TileDTO[]>([]);

    // Ingredient List Linking State
    const [selectedListId, setSelectedListId] = useState<number | null>(null);
    const [draftList, setDraftList] = useState<IngredientListCreateRequestDTO | null>(null);
    const [isSelectModalOpen, setIsSelectModalOpen] = useState(false);
    const [isDraftModalOpen, setIsDraftModalOpen] = useState(false);
    const [infoListId, setInfoListId] = useState<number | null>(null);
    const [lastCopiedId, setLastCopiedId] = useState<number | null>(null);

    if (initialData && initialData.id !== lastCopiedId) {
        setLastCopiedId(initialData.id);
        setName(initialData.name ? `${initialData.name} (Copy)` : 'Copy');
        setLayoutType(initialData.type);
        setSavedLayoutType(initialData.type);

        if (initialData.tiles && initialData.tiles.length > 0) {
            const maxX = Math.max(...initialData.tiles.map(t => t.x)) + 1;
            const maxY = Math.max(...initialData.tiles.map(t => t.y)) + 1;
            setDimensions({width: maxX, height: maxY});
            setTiles(initialData.tiles.map(t => ({...t, dispensed_types: t.dispensed_types || []})));
        } else {
            setDimensions({width: 3, height: 3});
            setTiles([]);
        }

        if (initialData.ingredient_list_id) {
            setSelectedListId(initialData.ingredient_list_id);
        } else {
            setSelectedListId(null);
        }
    }

    // Fetch details of selected list if an ID is present
    const {data: fullSelectedList} = useQuery({
        queryKey: ['ingredient_list_details', selectedListId],
        queryFn: () => getIngredientList(selectedListId!),
        enabled: !!selectedListId,
    });

    // Dynamically derive available ingredients from the active source
    const availableIngredients = useMemo(() => {
        if (draftList && draftList.ingredients) return draftList.ingredients.map(i => i.name).filter(Boolean);
        if (fullSelectedList && fullSelectedList.ingredients) return fullSelectedList.ingredients.map(i => i.name).filter(Boolean);
        return [];
    }, [draftList, fullSelectedList]);

    const availableIngredientsStr = availableIngredients.join('|');
    const [prevIngredientsStr, setPrevIngredientsStr] = useState(availableIngredientsStr);

    if (availableIngredientsStr !== prevIngredientsStr) {
        setPrevIngredientsStr(availableIngredientsStr);

        const cleanupTiles = (tileList: TileDTO[]) => tileList.map(t => {
            if (t.type === 'dispenser') {
                return {...t, dispensed_types: t.dispensed_types.filter(dt => availableIngredients.includes(dt))};
            }
            return t;
        });

        setTiles(prev => cleanupTiles(prev));
        setOrphanDispensers(prev => cleanupTiles(prev));
    }

    // UI Interaction State
    const [hoveredType, setHoveredType] = useState<string | null>(null);
    const [activeTileSelect, setActiveTileSelect] = useState<{ x: number, y: number } | null>(null);
    const [editingDispenser, setEditingDispenser] = useState<{ x: number, y: number } | null>(null);
    const [editingOrphanIndex, setEditingOrphanIndex] = useState<number | null>(null);

    // Query Mutation
    const mutation = useMutation({
        mutationFn: async (data: LayoutSingleCreateRequestDTO) => {
            setValidationErrors([]);
            await createLayout(data, true);
            return await createLayout(data, false);
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
            setLastCopiedId(null);
            onClose();
        },
        onError: (errors: unknown) => {
            if (Array.isArray(errors)) setValidationErrors(errors);
            else if (typeof errors === 'string') setValidationErrors([errors]);
            else setValidationErrors(["An unexpected error occurred while saving."]);
        }
    });

    const resetState = () => {
        setName('');
        setLayoutType(null);
        setSavedLayoutType(null);
        setDimensions({width: 3, height: 3});
        setIsConfiguring(false);
        setZoom(1);
        setTiles([]);
        setOrphanDispensers([]);
        setSelectedListId(null);
        setDraftList(null);
        setValidationErrors([]);
        setActiveTileSelect(null);
        setEditingDispenser(null);
        setEditingOrphanIndex(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleDiscard = () => {
        if (window.confirm("Are you sure you want to discard your changes?")) {
            resetState();
            onClose();
        }
    };

    const handleSubmit = () => {
        if (!layoutType) return;
        const payload: LayoutSingleCreateRequestDTO = {
            name: (name.trim() || null) as unknown as string,
            type: layoutType,
            tiles: tiles.map(tile => ({
                ...tile,
                dispensed_types: (tile.type === 'dispenser' ? tile.dispensed_types : null) as unknown as string[]
            })),
            ingredient_list_id: draftList ? null : (selectedListId ?? null),
            ingredient_list: draftList ? draftList : null
        };

        mutation.mutate(payload);
    };

    // Auto Zoom Logic
    const calculateAndSetZoom = (w: number, h: number) => {
        setTimeout(() => {
            if (gridContainerRef.current) {
                const padding = 32;
                const availableW = gridContainerRef.current.clientWidth - padding;
                const availableH = gridContainerRef.current.clientHeight - padding;
                const neededW = w * 80 + Math.max(0, w - 1) * 4;
                const neededH = h * 80 + Math.max(0, h - 1) * 4;

                if (neededW > 0 && neededH > 0) {
                    const scaleW = availableW / neededW;
                    const scaleH = availableH / neededH;
                    const newZoom = Math.min(1, scaleW, scaleH);
                    setZoom(Math.max(0.1, parseFloat(newZoom.toFixed(2))));
                }
            }
        }, 50);
    };

    // Setup Logic
    const generateGrid = (type: LayoutType, w: number, h: number) => {
        const newTiles: TileDTO[] = [];
        for (let y = 0; y < h; y++) {
            for (let x = 0; x < w; x++) {
                let tileType: TileType = 'empty';
                if (type === 'ring' && !isEdge(x, y, w, h)) {
                    tileType = 'blocked';
                }
                newTiles.push({x, y, type: tileType, dispensed_types: []});
            }
        }
        setTiles(newTiles);
        setLayoutType(type);
        setSavedLayoutType(type);
        setDimensions({width: w, height: h});
        calculateAndSetZoom(w, h);
    };

    const handleTypeSelectSubmit = (e: SyntheticEvent) => {
        e.preventDefault();
        if (!layoutType) return;

        const gridDispensers = tiles.filter(t => t.type === 'dispenser');
        if (gridDispensers.length > 0) {
            setOrphanDispensers(prev => [
                ...prev,
                ...gridDispensers.map(d => ({...d, x: -1, y: -1}))
            ]);
        }
        generateGrid(layoutType, dimensions.width, dimensions.height);
        setIsConfiguring(false);
    };

    const handleLayoutTypeChange = (type: LayoutType) => {
        setLayoutType(type);
        if (type === 'line') setDimensions(prev => ({width: prev.width, height: 1}));
        if (type === 'double_line') setDimensions(prev => ({width: prev.width, height: 2}));
        if (type === 'ring' || type === 'square') setDimensions(prev => ({width: prev.width, height: prev.width}));
    };

    const handleCancelConfig = () => {
        setIsConfiguring(false);
        if (tiles.length === 0) {
            setLayoutType(null);
        } else {
            setLayoutType(savedLayoutType);
            const maxX = Math.max(...tiles.map(t => t.x)) + 1;
            const maxY = Math.max(...tiles.map(t => t.y)) + 1;
            setDimensions({width: maxX, height: maxY});
        }
    };

    const clearGrid = () => {
        const toOrphans = tiles.filter(t => t.type === 'dispenser');
        setOrphanDispensers(prev => [...prev, ...toOrphans]);

        setTiles(prev => prev.map(t => {
            if (t.type === 'empty' || (t.type === 'blocked' && layoutType !== 'custom')) return t;
            return {...t, type: 'empty', dispensed_types: []};
        }));
    };

    // Grid Interactions
    const updateTile = (x: number, y: number, data: Partial<TileDTO>) => {
        setTiles(prev => prev.map(t => (t.x === x && t.y === y) ? {...t, ...data} : t));
    };

    const moveOrphanToGrid = (orphanIndex: number, destX: number, destY: number) => {
        const orphan = orphanDispensers[orphanIndex];
        const targetTile = tiles.find(t => t.x === destX && t.y === destY);
        if (!targetTile || targetTile.type === 'blocked') return;

        if (targetTile.type === 'dispenser') {
            setOrphanDispensers(prev => [...prev.filter((_, i) => i !== orphanIndex), {...targetTile, x: -1, y: -1}]);
        } else {
            setOrphanDispensers(prev => prev.filter((_, i) => i !== orphanIndex));
        }
        updateTile(destX, destY, {type: 'dispenser', dispensed_types: orphan.dispensed_types});
    };

    const moveGridTile = (srcX: number, srcY: number, destX: number, destY: number) => {
        if (srcX === destX && srcY === destY) return;

        const srcTile = tiles.find(t => t.x === srcX && t.y === srcY);
        const destTile = tiles.find(t => t.x === destX && t.y === destY);

        if (!srcTile || !destTile || srcTile.type === 'blocked' || destTile.type === 'blocked') return;

        setTiles(prev => prev.map(t => {
            if (t.x === srcX && t.y === srcY) return {
                ...t,
                type: destTile.type,
                dispensed_types: destTile.dispensed_types
            };
            if (t.x === destX && t.y === destY) return {
                ...t,
                type: srcTile.type,
                dispensed_types: srcTile.dispensed_types
            };
            return t;
        }));
    };

    // Drag and Drop Handlers
    const handleDragStart = (e: React.DragEvent, type: string, payload: unknown) => {
        e.dataTransfer.setData('type', type);
        e.dataTransfer.setData('payload', JSON.stringify(payload));
    };

    const handleDrop = (e: React.DragEvent, destX: number, destY: number) => {
        e.preventDefault();
        const type = e.dataTransfer.getData('type');
        const payloadStr = e.dataTransfer.getData('payload');
        if (!payloadStr) return;

        const payload = JSON.parse(payloadStr);
        const targetTile = tiles.find(t => t.x === destX && t.y === destY);
        if (!targetTile) return;

        if (type === 'dispensedType') {
            if (targetTile.type === 'dispenser' && !targetTile.dispensed_types.includes(payload.name)) {
                updateTile(destX, destY, {dispensed_types: [...targetTile.dispensed_types, payload.name]});
            }
        } else if (type === 'orphan') {
            moveOrphanToGrid(payload.index, destX, destY);
        } else if (type === 'gridTile') {
            moveGridTile(payload.x, payload.y, destX, destY);
        }
    };

    const handleOrphanListDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const type = e.dataTransfer.getData('type');
        if (type === 'gridTile') {
            const payload = JSON.parse(e.dataTransfer.getData('payload'));
            const srcTile = tiles.find(t => t.x === payload.x && t.y === payload.y);
            if (srcTile && srcTile.type === 'dispenser') {
                setOrphanDispensers(prev => [...prev, {...srcTile, x: -1, y: -1}]);
                updateTile(payload.x, payload.y, {type: 'empty', dispensed_types: []});
            }
        }
    };

    const handleOrphanDrop = (e: React.DragEvent, orphanIndex: number) => {
        e.preventDefault();
        e.stopPropagation();
        const type = e.dataTransfer.getData('type');
        const payloadStr = e.dataTransfer.getData('payload');
        if (!payloadStr) return;

        const payload = JSON.parse(payloadStr);
        if (type === 'dispensedType') {
            setOrphanDispensers(prev => prev.map((orphan, i) => {
                if (i === orphanIndex && !orphan.dispensed_types.includes(payload.name)) {
                    return {...orphan, dispensed_types: [...orphan.dispensed_types, payload.name]};
                }
                return orphan;
            }));
        }
    };

    const handleClearIngredientList = () => {
        if (!draftList && !selectedListId) return;
        if (window.confirm("Are you sure you want to remove the ingredient list? This will remove all assigned ingredients from your dispensers on the grid.")) {
            setSelectedListId(null);
            setDraftList(null);
        }
    };

    // Shared Edit Modal Logic
    let editTile: TileDTO | undefined;
    let updateEditTile: ((newTypes: string[]) => void) | undefined;
    let closeEditModal: (() => void) | undefined;

    if (editingDispenser) {
        editTile = tiles.find(t => t.x === editingDispenser.x && t.y === editingDispenser.y);
        updateEditTile = (newTypes) => updateTile(editingDispenser.x, editingDispenser.y, {dispensed_types: newTypes});
        closeEditModal = () => setEditingDispenser(null);
    } else if (editingOrphanIndex !== null) {
        editTile = orphanDispensers[editingOrphanIndex];
        updateEditTile = (newTypes) => {
            setOrphanDispensers(prev => prev.map((o, idx) => idx === editingOrphanIndex ? {
                ...o,
                dispensed_types: newTypes
            } : o));
        };
        closeEditModal = () => setEditingOrphanIndex(null);
    }

    // Computed
    const counts = tiles.reduce((acc, tile) => {
        acc[tile.type]++;
        return acc;
    }, {empty: 0, interface: 0, blocked: 0, dispenser: 0, mixer: 0, capper: 0});

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col max-h-[95vh] h-225">

                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0 relative">
                    <h2 className="text-xl font-bold text-gray-900 w-1/3">Create Layout</h2>
                    <div className="w-1/3 flex justify-end items-center gap-4 ml-auto">
                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
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
                        <ul className="text-sm text-red-700 list-disc pl-5">
                            {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}

                <div className="flex-1 min-h-0 bg-gray-50 relative p-6">
                    {!layoutType ? (
                        <div className="h-full flex items-center justify-center">
                            <button
                                onClick={() => setIsConfiguring(true)}
                                className="px-6 py-3 bg-black text-white rounded-lg shadow hover:bg-black font-medium text-lg"
                            >
                                Choose Type
                            </button>
                        </div>
                    ) : (
                        <div className="h-full flex gap-6">

                            {/* Left Side */}
                            <div className="w-52 flex flex-col gap-4 shrink-0 h-full">
                                <div
                                    className="bg-white border border-gray-200 rounded-md shadow-sm p-4 flex flex-col gap-4 shrink-0">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-1">Name</label>
                                        <input
                                            type="text"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            placeholder="Layout name..."
                                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-gray-500 focus:border-gray-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-1">Layout
                                            Type</label>
                                        <div
                                            className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded px-2 py-1.5">
                                            <span className="text-sm font-medium text-gray-700 uppercase tracking-wide">
                                                {savedLayoutType?.replace('_', ' ')}
                                            </span>
                                            <button
                                                onClick={() => setIsConfiguring(true)}
                                                className="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors"
                                                title="Edit Layout"
                                            >
                                                <PencilSquareIcon className="w-4 h-4"/>
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Ingredient List Linking Panel */}
                                <div
                                    className="flex flex-col flex-1 min-h-0 bg-white border border-gray-200 rounded-md shadow-sm overflow-hidden">
                                    <div
                                        className="p-3 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
                                        <span className="font-semibold text-sm text-gray-800">Ingredients</span>
                                        <div className="flex gap-1">
                                            <button
                                                onClick={() => setIsSelectModalOpen(true)}
                                                className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                                title="Select existing ingredient list"
                                            >
                                                <MagnifyingGlassIcon className="w-4 h-4"/>
                                            </button>
                                            <button
                                                onClick={() => setIsDraftModalOpen(true)}
                                                className="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors"
                                                title="Edit / Create ingredient list"
                                            >
                                                <PencilSquareIcon className="w-4 h-4"/>
                                            </button>
                                            <button
                                                onClick={handleClearIngredientList}
                                                disabled={!draftList && !selectedListId}
                                                className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-500"
                                                title="Remove ingredient list"
                                            >
                                                <TrashIcon className="w-4 h-4"/>
                                            </button>
                                        </div>
                                    </div>

                                    <div
                                        className="bg-white border-b border-gray-100 p-2 text-xs font-medium text-center text-gray-600 truncate">
                                        {draftList ? `${draftList.name || 'Unnamed'} (Draft)` : fullSelectedList?.name ? fullSelectedList.name : 'No list selected'}
                                    </div>

                                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                                        {availableIngredients.map(t => (
                                            <div
                                                key={t}
                                                draggable
                                                onDragStart={(e) => handleDragStart(e, 'dispensedType', {name: t})}
                                                onMouseEnter={() => setHoveredType(t)}
                                                onMouseLeave={() => setHoveredType(null)}
                                                className="flex items-center justify-between p-2.5 bg-gray-50 border border-gray-200 rounded text-sm cursor-grab active:cursor-grabbing hover:bg-gray-100 transition-colors"
                                            >
                                                <span className="truncate flex-1 font-medium text-gray-700"
                                                      title={t}>{t}</span>
                                            </div>
                                        ))}
                                        {availableIngredients.length === 0 && (
                                            <p className="text-xs text-gray-400 text-center mt-4 p-2">Select or create a
                                                list to add ingredients.</p>
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
                                            {tiles.map((tile) => {
                                                const isHighlighted = hoveredType && tile.type === 'dispenser' && (tile.dispensed_types || []).includes(hoveredType);
                                                return (
                                                    <div
                                                        key={`${tile.x}-${tile.y}`}
                                                        className={`w-full h-full border flex flex-col items-center justify-center relative select-none transition-colors
                                                            ${tile.type === 'empty' ? 'bg-white border-gray-300 hover:bg-gray-100 text-gray-300' : ''}
                                                            ${tile.type === 'blocked' ? 'bg-gray-800 border-gray-900 text-white' : ''}
                                                            ${tile.type === 'interface' ? 'bg-blue-50 border-blue-300 text-blue-600 shadow-sm' : ''}
                                                            ${tile.type === 'mixer' ? 'bg-green-50 border-green-300 text-green-600 shadow-sm' : ''}
                                                            ${tile.type === 'capper' ? 'bg-red-50 border-red-300 text-red-600 shadow-sm' : ''}
                                                            ${tile.type === 'dispenser' ? (isHighlighted ? 'bg-green-100 border-green-500 text-green-700 shadow-md ring-2 ring-green-300' : 'bg-orange-50 border-orange-300 text-orange-600 shadow-sm') : ''}
                                                        `}
                                                        draggable={tile.type !== 'blocked'}
                                                        onDragStart={(e) => handleDragStart(e, 'gridTile', {
                                                            x: tile.x,
                                                            y: tile.y
                                                        })}
                                                        onDragOver={(e) => e.preventDefault()}
                                                        onDrop={(e) => handleDrop(e, tile.x, tile.y)}
                                                        onClick={() => {
                                                            if (tile.type === 'empty') setActiveTileSelect({
                                                                x: tile.x,
                                                                y: tile.y
                                                            });
                                                        }}
                                                        title={tile.type === 'dispenser' ? (tile.dispensed_types || []).join('\n') : ''}
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

                                                        {(['interface', 'mixer', 'capper'].includes(tile.type) || (tile.type === 'blocked' && layoutType === 'custom')) && zoom > 0.4 && (
                                                            <button
                                                                className="absolute bottom-1 right-1 z-20 text-xs bg-white text-gray-500 rounded-full w-5 h-5 flex items-center justify-center border hover:text-red-500 hover:border-red-500 hover:bg-red-50 shadow-sm"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    updateTile(tile.x, tile.y, {type: 'empty'});
                                                                }}><TrashIcon className="w-3.5 h-3.5"/></button>
                                                        )}

                                                        {tile.type === 'dispenser' && zoom > 0.4 && (
                                                            <>
                                                                <button
                                                                    className="absolute bottom-1 right-1 z-20 text-xs bg-white text-gray-500 rounded-full w-5 h-5 flex items-center justify-center border hover:text-red-500 hover:border-red-500 hover:bg-red-50 shadow-sm"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        updateTile(tile.x, tile.y, {
                                                                            type: 'empty',
                                                                            dispensed_types: []
                                                                        });
                                                                    }}><TrashIcon className="w-3.5 h-3.5"/></button>
                                                                <button
                                                                    className="absolute bottom-1 left-1 z-20 text-xs bg-white text-gray-500 rounded w-5 h-5 flex items-center justify-center border hover:text-blue-600 hover:border-blue-500 hover:bg-blue-50 shadow-sm"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setEditingDispenser({x: tile.x, y: tile.y});
                                                                    }}><PencilSquareIcon className="w-3.5 h-3.5"/>
                                                                </button>
                                                            </>
                                                        )}

                                                        {activeTileSelect?.x === tile.x && activeTileSelect?.y === tile.y && (
                                                            <div
                                                                className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 bg-white border border-gray-200 shadow-xl rounded-md flex gap-1.5 p-2">
                                                                <button
                                                                    className="p-2 hover:bg-blue-50 text-blue-600 rounded-md"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        updateTile(tile.x, tile.y, {type: 'interface'});
                                                                        setActiveTileSelect(null);
                                                                    }}><TruckIcon className="w-6 h-6"/></button>
                                                                <button
                                                                    className="p-2 hover:bg-orange-50 text-orange-600 rounded-md"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        updateTile(tile.x, tile.y, {
                                                                            type: 'dispenser',
                                                                            dispensed_types: []
                                                                        });
                                                                        setActiveTileSelect(null);
                                                                    }}
                                                                >
                                                                    <FunnelIcon className="w-6 h-6"/>
                                                                </button>
                                                                <button
                                                                    className="p-2 hover:bg-green-50 text-green-600 rounded-md"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        updateTile(tile.x, tile.y, {type: 'mixer'});
                                                                        setActiveTileSelect(null);
                                                                    }}><ArrowPathIcon className="w-6 h-6"/></button>
                                                                <button
                                                                    className="p-2 hover:bg-red-50 text-red-600 rounded-md"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        updateTile(tile.x, tile.y, {type: 'capper'});
                                                                        setActiveTileSelect(null);
                                                                    }}><CircleStackIcon className="w-6 h-6"/></button>

                                                                {layoutType === 'custom' && (
                                                                    <button
                                                                        className="p-2 hover:bg-gray-100 text-gray-800 rounded-md"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            updateTile(tile.x, tile.y, {type: 'blocked'});
                                                                            setActiveTileSelect(null);
                                                                        }}><XCircleIcon className="w-6 h-6"/></button>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right Side */}
                            <div className="w-48 flex flex-col gap-4 shrink-0 h-full">
                                <div
                                    className="bg-white border border-gray-200 rounded-md shadow-sm p-4 flex flex-col gap-3 shrink-0">
                                    <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2">Layout
                                        Statistics</h3>
                                    <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-sm text-gray-600">
                                        <div className="flex items-center gap-2">
                                            <div className="text-blue-500"><TruckIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.interface}</span></div>
                                        <div className="flex items-center gap-2">
                                            <div className="text-orange-500"><FunnelIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.dispenser}</span></div>
                                        <div className="flex items-center gap-2">
                                            <div className="text-green-500"><ArrowPathIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.mixer}</span></div>
                                        <div className="flex items-center gap-2">
                                            <div className="text-red-500"><CircleStackIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.capper}</span></div>
                                        <div className="flex items-center gap-2">
                                            <div className="text-gray-400"><PlusCircleIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.empty}</span></div>
                                        <div className="flex items-center gap-2">
                                            <div className="text-gray-800"><XCircleIcon className="w-5 h-5"/></div>
                                            <span className="font-medium">{counts.blocked}</span></div>
                                    </div>
                                </div>

                                <div
                                    className="flex flex-col flex-1 min-h-0 bg-white border border-gray-200 rounded-md shadow-sm overflow-hidden"
                                    onDragOver={(e) => e.preventDefault()} onDrop={handleOrphanListDrop}>
                                    <div className="p-3 border-b border-gray-200 bg-gray-50 flex flex-col gap-2">
                                        <span className="font-semibold text-sm text-gray-800">Replaced Dispensers</span>
                                        <button onClick={clearGrid}
                                                className="w-full px-2 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded hover:bg-red-50 hover:text-red-600 hover:border-red-300 transition-colors">Clear
                                            Grid
                                        </button>
                                    </div>
                                    <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50/50">
                                        {orphanDispensers.length === 0 &&
                                            <p className="text-xs text-gray-400 text-center mt-4">Drag dispensers here
                                                to put them aside.</p>}
                                        {orphanDispensers.map((orphan, i) => {
                                            const count = orphan.dispensed_types?.length || 0;
                                            const initials = count > 0 ? getDispenserInitials(orphan.dispensed_types) : '';
                                            const isHighlighted = hoveredType && orphan.dispensed_types.includes(hoveredType);

                                            return (
                                                <div key={i} draggable
                                                     onDragStart={(e) => handleDragStart(e, 'orphan', {index: i})}
                                                     onDragOver={(e) => e.preventDefault()}
                                                     onDrop={(e) => handleOrphanDrop(e, i)}
                                                     className={`w-full border rounded-md flex flex-col items-center justify-center p-3 cursor-grab active:cursor-grabbing transition-all group relative ${isHighlighted ? 'bg-green-100 border-green-500 shadow-md ring-2 ring-green-300' : 'bg-white border-orange-200 shadow-sm hover:border-orange-400 hover:shadow'}`}
                                                     title={orphan.dispensed_types.join('\n')}>
                                                    <button onClick={(e) => {
                                                        e.stopPropagation();
                                                        setEditingOrphanIndex(i);
                                                    }}
                                                            className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-600 p-1">
                                                        <PencilSquareIcon className="w-3.5 h-3.5"/></button>
                                                    <FunnelIcon
                                                        className={`w-7 h-7 mb-2 ${isHighlighted ? 'text-green-700' : 'text-orange-500'}`}/>
                                                    <span
                                                        className={`text-[11px] font-medium px-2 py-0.5 rounded-full truncate max-w-full text-center ${isHighlighted ? 'text-green-800 bg-green-200' : 'text-orange-800 bg-orange-100'}`}>{count > 0 ? (initials ? `${initials} (${count})` : `(${count})`) : '(0)'}</span>
                                                    <button
                                                        onClick={() => setOrphanDispensers(prev => prev.filter((_, idx) => idx !== i))}
                                                        className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 p-1">
                                                        <TrashIcon className="w-3.5 h-3.5"/></button>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <IngredientListSelectModal
                        isOpen={isSelectModalOpen}
                        onClose={() => setIsSelectModalOpen(false)}
                        onSelect={(id) => {
                            setSelectedListId(id);
                            setDraftList(null);
                            setIsSelectModalOpen(false);
                        }}
                        onInfo={(id) => setInfoListId(id)}
                    />

                    <IngredientListInfoModal
                        listId={infoListId}
                        onClose={() => setInfoListId(null)}
                    />

                    <LayoutIngredientListDraftModal
                        isOpen={isDraftModalOpen}
                        initialData={draftList || fullSelectedList}
                        onClose={() => setIsDraftModalOpen(false)}
                        onSuccessDraft={(payload) => {
                            setDraftList(payload);
                            setSelectedListId(null);
                            setIsDraftModalOpen(false);
                        }}
                    />

                    {isConfiguring && (
                        <div
                            className="absolute inset-0 bg-white/90 backdrop-blur-sm z-30 flex items-center justify-center">
                            <form onSubmit={handleTypeSelectSubmit}
                                  className="bg-white p-6 rounded-xl shadow-2xl border border-gray-200 w-100 space-y-5">
                                <h3 className="text-xl font-bold text-gray-900 border-b border-gray-100 pb-3">{tiles.length > 0 ? 'Change Layout' : 'Setup Layout'}</h3>
                                {tiles.length > 0 && <div
                                    className="p-3 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">Changing
                                    the layout will safely move all existing dispensers to the "Replaced Dispensers"
                                    section and keep all ingredients.</div>}

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">Layout
                                        Type</label>
                                    <select
                                        className="w-full border-gray-300 rounded-md border p-2.5 focus:ring-gray-500 focus:border-gray-500"
                                        value={layoutType || ''}
                                        onChange={(e) => handleLayoutTypeChange(e.target.value as LayoutType)} required>
                                        <option value="" disabled>Select a type...</option>
                                        <option value="line">Line</option>
                                        <option value="double_line">Double Line</option>
                                        <option value="square">Square</option>
                                        <option value="ring">Ring</option>
                                        <option value="custom">Custom</option>
                                    </select>
                                </div>

                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                                            {layoutType === 'ring' || layoutType === 'square' ? 'Size' : 'Width'}
                                        </label>
                                        <input type="number" min="1" max="100" value={dimensions.width}
                                               onChange={(e) => {
                                                   const val = parseInt(e.target.value) || 1;
                                                   setDimensions(d => ({
                                                       ...d,
                                                       width: val,
                                                       height: (layoutType === 'ring' || layoutType === 'square') ? val : d.height
                                                   }));
                                               }}
                                               className="w-full border-gray-300 rounded-md border p-2.5 focus:ring-gray-500 focus:border-gray-500"
                                               required/>
                                    </div>
                                    {layoutType !== 'ring' && layoutType !== 'square' && (
                                        <div className="flex-1">
                                            <label
                                                className="block text-sm font-semibold text-gray-700 mb-1.5">Height</label>
                                            <input type="number" min="1" max="100" value={dimensions.height}
                                                   onChange={(e) => setDimensions(d => ({
                                                       ...d,
                                                       height: parseInt(e.target.value) || 1
                                                   }))}
                                                   className="w-full border-gray-300 rounded-md border p-2.5 disabled:bg-gray-100 focus:ring-gray-500 focus:border-gray-500"
                                                   disabled={layoutType === 'line' || layoutType === 'double_line'}
                                                   required/>
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                    <button type="button" onClick={handleCancelConfig}
                                            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium">Cancel
                                    </button>
                                    <button type="submit"
                                            className="px-5 py-2 bg-black text-white rounded-md hover:bg-black font-medium shadow-sm">Confirm
                                        Setup
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {editTile && updateEditTile && closeEditModal && (
                        <div
                            className="absolute inset-0 bg-black/20 backdrop-blur-[1px] z-40 flex items-center justify-center">
                            <div className="bg-white p-5 rounded-lg shadow-xl border border-gray-200 w-80">
                                <h4 className="font-bold text-gray-800 mb-4 border-b border-gray-100 pb-2">Edit
                                    Ingredients</h4>
                                <div className="space-y-2 max-h-56 overflow-y-auto mb-5 pr-1">
                                    {editTile.dispensed_types.length === 0 ?
                                        <p className="text-gray-400 text-sm italic text-center py-2">No types
                                            assigned.</p> : null}
                                    {editTile.dispensed_types.map(dt => (
                                        <div key={dt}
                                             className="flex justify-between items-center text-sm bg-gray-50 p-2 border border-gray-200 rounded">
                                            <span className="truncate font-medium text-gray-700">{dt}</span>
                                            <button
                                                onClick={() => updateEditTile!(editTile!.dispensed_types.filter(t => t !== dt))}
                                                className="text-red-500 hover:bg-red-50 p-1 rounded">✕
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <button onClick={closeEditModal}
                                        className="w-full bg-gray-800 hover:bg-gray-700 text-white rounded-md py-2 font-medium">Done
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div
                    className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end space-x-3 shrink-0">
                    <div className="flex space-x-3">
                        <button type="button" onClick={handleDiscard}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                            Discard Changes
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={mutation.isPending || !layoutType || (!draftList && !selectedListId)}
                            className="px-5 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center transition-colors shadow-sm"
                        >
                            {mutation.isPending ? 'Validating...' : 'Create Layout'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}