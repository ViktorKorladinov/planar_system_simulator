import * as React from 'react';
import {forwardRef, type SyntheticEvent, useEffect, useImperativeHandle, useMemo, useRef, useState} from 'react';
import {useMutation, useQuery} from '@tanstack/react-query';
import {createLayout} from '../../../api/layouts';
import {getIngredientList} from '../../../api/ingredient_lists';
import type {LayoutSingleCreateRequestDTO, LayoutType, TileDTO, TileType} from '../../../types/layouts';
import type {EntityState} from '../ExperimentCreateModal';
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
import IngredientListSelectModal from "../../ingredient_lists/IngredientListSelectModal";
import LayoutIngredientListDraftModal from "../../layouts/LayoutIngredientListDraftModal";
import IngredientListInfoModal from '../../ingredient_lists/IngredientListInfoModal';
import LayoutSelectModal from "../../layouts/LayoutSelectModal";

interface Props {
    state: EntityState<LayoutSingleCreateRequestDTO>;
    setState: (updater: (prev: EntityState<LayoutSingleCreateRequestDTO>) => EntityState<LayoutSingleCreateRequestDTO>) => void;
}

export interface LayoutTabRef {
    discard: () => void;
    validate: () => Promise<LayoutSingleCreateRequestDTO | null>;
}

const INITIAL_FORM_STATE: LayoutSingleCreateRequestDTO = {
    name: '', type: 'custom' as LayoutType, tiles: [], ingredient_list_id: null, ingredient_list: null
};

// Helpers
const isEdge = (x: number, y: number, w: number, h: number) => x === 0 || y === 0 || x === w - 1 || y === h - 1;
const getDispenserInitials = (types: string[]) => {
    if (!types || !Array.isArray(types) || types.length === 0) return '';
    const result = [...types].sort((a, b) => a.localeCompare(b)).slice(0, 5).map(t => (typeof t === 'string' && t.length > 0) ? t.charAt(0).toUpperCase() : '').filter(Boolean).join(',')
    if (types.length > 5) return result + '...'
    return result
};

const ExperimentLayoutTab = forwardRef<LayoutTabRef, Props>(({state, setState}, ref) => {
    const gridContainerRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [validationErrors, setValidationErrors] = useState<string[]>([]);
    const [isSelectModalOpen, setIsSelectModalOpen] = useState(false);

    // Grid Local State
    const [isConfiguring, setIsConfiguring] = useState(false);
    const [tempDimensions, setTempDimensions] = useState({width: 3, height: 3});
    const [tempLayoutType, setTempLayoutType] = useState<LayoutType | null>(null);
    const [zoom, setZoom] = useState(1);
    const [orphanDispensers, setOrphanDispensers] = useState<TileDTO[]>([]);

    // Ingredient Linking State
    const [isIngListSelectModalOpen, setIsIngListSelectModalOpen] = useState(false);
    const [isIngListDraftModalOpen, setIsIngListDraftModalOpen] = useState(false);
    const [infoListId, setInfoListId] = useState<number | null>(null);

    // Interaction State
    const [hoveredType, setHoveredType] = useState<string | null>(null);
    const [activeTileSelect, setActiveTileSelect] = useState<{ x: number, y: number } | null>(null);
    const [editingDispenser, setEditingDispenser] = useState<{ x: number, y: number } | null>(null);
    const [editingOrphanIndex, setEditingOrphanIndex] = useState<number | null>(null);

    const performValidation = async () => {
        if (!state.data) return null;
        setState(prev => ({...prev, isValidating: true}));
        const isDraftIngList = state.data.ingredient_list && !('id' in state.data.ingredient_list);

        const payload: LayoutSingleCreateRequestDTO = {
            name: state.data.name?.trim() || (null as unknown as string),
            type: state.data.type,
            tiles: (state.data.tiles || []).map(t => ({
                x: t.x,
                y: t.y,
                type: t.type,
                dispensed_types: t.type === 'dispenser' ? t.dispensed_types : (null as unknown as string[])
            })),
            ingredient_list_id: isDraftIngList ? null : (state.data.ingredient_list_id ?? (state.data.ingredient_list as {
                id?: number
            })?.id ?? null),
            ingredient_list: isDraftIngList ? state.data.ingredient_list : null
        };

        try {
            return await validateMutation.mutateAsync(payload);
        } catch {
            return null;
        }
    };

    useImperativeHandle(ref, () => ({
        discard: () => {
            setState(() => ({mode: 'empty', id: null, data: null, isValidated: false, isValidating: false}));
            setValidationErrors([]);
            setOrphanDispensers([]);
            setIsConfiguring(false);
        },
        validate: async () => {
            if (state.isValidated && state.data) return state.data as LayoutSingleCreateRequestDTO;
            return await performValidation();
        }
    }));

    const updateData = (updates: Partial<LayoutSingleCreateRequestDTO>) => {
        setState(prev => ({
            ...prev,
            mode: 'draft',
            isValidated: false,
            isValidating: false,
            data: {...(prev.data || INITIAL_FORM_STATE), ...updates}
        }));
    };

    const validateMutation = useMutation({
        mutationFn: async (data: LayoutSingleCreateRequestDTO) => {
            setValidationErrors([]);
            await createLayout(data, true);
            return data;
        },
        onSuccess: (sanitizedData) => {
            setState(prev => ({...prev, data: sanitizedData, isValidated: true, isValidating: false}));
        },
        onError: (errors: unknown) => {
            setState(prev => ({...prev, isValidated: false, isValidating: false}));
            if (Array.isArray(errors)) setValidationErrors(errors);
            else setValidationErrors(["Validation failed."]);
        }
    });

    const handleValidate = async (e: SyntheticEvent) => {
        e.preventDefault();
        await performValidation();
    };

    const currentData = state.data || INITIAL_FORM_STATE;
    const tiles = useMemo(() => currentData.tiles || [], [currentData.tiles]);

    const renderDimensions = useMemo(() => ({
        width: Math.max(...tiles.map(t => t.x)) + 1 || 1,
        height: Math.max(...tiles.map(t => t.y)) + 1 || 1
    }), [tiles]);

    // Auto Zoom
    useEffect(() => {
        const container = gridContainerRef.current;
        if (!container || renderDimensions.width === 0) return;

        const padding = 36;
        const availableW = container.clientWidth - padding;
        const availableH = container.clientHeight - padding;

        if (availableW <= 0 || availableH <= 0) return;

        const neededW = renderDimensions.width * 80 + Math.max(0, renderDimensions.width - 1) * 4;
        const neededH = renderDimensions.height * 80 + Math.max(0, renderDimensions.height - 1) * 4;

        if (neededW > 0 && neededH > 0) {
            const calculatedZoom = Math.floor(Math.min(1, availableW / neededW, availableH / neededH) * 100) / 100;
            setZoom(Math.max(0.1, calculatedZoom));
        }
    }, [renderDimensions.width, renderDimensions.height, isConfiguring]);

    // Setup Logic
    const handleCreateNew = () => {
        setTempLayoutType('custom');
        setTempDimensions({width: 3, height: 3});
        setIsConfiguring(true);
    };

    const handleCancelSetup = () => {
        setIsConfiguring(false);
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const text = event.target?.result as string;
                const json = JSON.parse(text);
                const placement = json.placement || (json.layout && json.layout.placement) || null;
                if (!placement || !Array.isArray(placement)) {
                    setValidationErrors(["Invalid file format. 'placement' array is missing."]);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                    return;
                }

                const height = placement.length;
                const width = height > 0 ? placement[0].length : 0;
                
                const uniqueIngredients = new Set<string>();
                const newTiles: TileDTO[] = [];
                for (let y = 0; y < height; y++) {
                    for (let x = 0; x < width; x++) {
                        const cell = placement[y][x];
                        if (cell === 'interface') {
                            newTiles.push({x, y, type: 'interface', dispensed_types: []});
                        } else if (!cell || cell === 'empty') {
                            newTiles.push({x, y, type: 'empty', dispensed_types: []});
                        } else if (cell === 'blocked') {
                            newTiles.push({x, y, type: 'blocked', dispensed_types: []});
                        } else {
                            const dispensed = cell.split(',').map((s: string) => s.trim()).filter(Boolean);
                            dispensed.forEach((d: string) => uniqueIngredients.add(d));
                            newTiles.push({x, y, type: 'dispenser', dispensed_types: dispensed});
                        }
                    }
                }
                
                const newIngredientList = {
                    name: `${file.name.replace('.json', '')} Ingredients`,
                    type: 'medicine' as const,
                    ingredients: Array.from(uniqueIngredients).map(name => ({
                        name,
                        note_type: null,
                        viscosity: null,
                        volatility_rank: null
                    }))
                };

                setState(() => ({
                    mode: 'draft',
                    id: null,
                    isValidated: false,
                    isValidating: false,
                    data: { 
                        ...INITIAL_FORM_STATE, 
                        name: file.name.replace('.json', ''), 
                        type: 'custom', 
                        tiles: newTiles,
                        ingredient_list_id: null,
                        ingredient_list: newIngredientList as any
                    }
                }));
                setValidationErrors([]);
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'Invalid JSON';
                setValidationErrors([`Failed to parse file: ${errorMessage}`]);
            }
            if (fileInputRef.current) fileInputRef.current.value = '';
        };
        reader.readAsText(file);
    };

    const handleTypeSelectSubmit = (e: SyntheticEvent) => {
        e.preventDefault();
        if (!tempLayoutType) return;

        const gridDispensers = tiles.filter(t => t.type === 'dispenser');
        if (gridDispensers.length > 0) {
            setOrphanDispensers(prev => [...prev, ...gridDispensers.map(d => ({...d, x: -1, y: -1}))]);
        }

        const newTiles: TileDTO[] = [];
        for (let y = 0; y < tempDimensions.height; y++) {
            for (let x = 0; x < tempDimensions.width; x++) {
                let tileType: TileType = 'empty';
                if (tempLayoutType === 'ring' && !isEdge(x, y, tempDimensions.width, tempDimensions.height)) {
                    tileType = 'blocked';
                }
                newTiles.push({x, y, type: tileType, dispensed_types: []});
            }
        }

        if (state.mode === 'empty') {
            setState(() => ({
                mode: 'draft',
                id: null,
                isValidated: false,
                isValidating: false,
                data: {...INITIAL_FORM_STATE, type: tempLayoutType, tiles: newTiles}
            }));
        } else {
            updateData({type: tempLayoutType, tiles: newTiles});
        }
        setIsConfiguring(false);
    };

    // Ingredient Derivation
    const {data: fullSelectedList} = useQuery({
        queryKey: ['ingredient_list_details', currentData.ingredient_list_id],
        queryFn: () => getIngredientList(currentData.ingredient_list_id!),
        enabled: !!currentData.ingredient_list_id,
    });

    const availableIngredients = useMemo(() => {
        if (currentData.ingredient_list && currentData.ingredient_list.ingredients) return currentData.ingredient_list.ingredients.map(i => i.name).filter(Boolean);
        if (fullSelectedList && fullSelectedList.ingredients) return fullSelectedList.ingredients.map(i => i.name).filter(Boolean);
        return [];
    }, [currentData.ingredient_list, fullSelectedList]);

    const availableIngredientsStr = availableIngredients.join('|');
    const [prevIngredientsStr, setPrevIngredientsStr] = useState(availableIngredientsStr);

    if (availableIngredientsStr !== prevIngredientsStr) {
        setPrevIngredientsStr(availableIngredientsStr);

        if (state.mode !== 'empty') {
            let hasChanges = false;

            const cleanupTiles = (tileList: TileDTO[]) => tileList.map(t => {
                if (t.type === 'dispenser') {
                    const originalLen = t.dispensed_types.length;
                    const filtered = t.dispensed_types.filter(dt => availableIngredients.includes(dt));
                    if (filtered.length !== originalLen) hasChanges = true;
                    return {...t, dispensed_types: filtered};
                }
                return t;
            });

            const newTiles = cleanupTiles(tiles);
            const newOrphans = cleanupTiles(orphanDispensers);

            if (hasChanges) {
                updateData({tiles: newTiles});
                setOrphanDispensers(newOrphans);
            }
        }
    }

    // Grid Actions
    const updateTile = (x: number, y: number, data: Partial<TileDTO>) => {
        updateData({tiles: tiles.map(t => (t.x === x && t.y === y) ? {...t, ...data} : t)});
    };

    const moveOrphanToGrid = (orphanIndex: number, destX: number, destY: number) => {
        const orphan = orphanDispensers[orphanIndex];
        const targetTile = tiles.find(t => t.x === destX && t.y === destY);
        if (!targetTile || targetTile.type === 'blocked') return;
        if (targetTile.type === 'dispenser') setOrphanDispensers(prev => [...prev.filter((_, i) => i !== orphanIndex), {
            ...targetTile,
            x: -1,
            y: -1
        }]);
        else setOrphanDispensers(prev => prev.filter((_, i) => i !== orphanIndex));
        updateTile(destX, destY, {type: 'dispenser', dispensed_types: orphan.dispensed_types});
    };

    const moveGridTile = (srcX: number, srcY: number, destX: number, destY: number) => {
        if (srcX === destX && srcY === destY) return;
        const srcTile = tiles.find(t => t.x === srcX && t.y === srcY);
        const destTile = tiles.find(t => t.x === destX && t.y === destY);
        if (!srcTile || !destTile || srcTile.type === 'blocked' || destTile.type === 'blocked') return;
        updateData({
            tiles: tiles.map(t => {
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
            })
        });
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
        } else if (type === 'orphan') moveOrphanToGrid(payload.index, destX, destY);
        else if (type === 'gridTile') moveGridTile(payload.x, payload.y, destX, destY);
    };

    const configModal = isConfiguring && (
        <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-30 flex items-center justify-center">
            <form onSubmit={handleTypeSelectSubmit}
                  className="bg-white p-6 rounded-xl shadow-2xl border border-gray-200 w-100 space-y-5">
                <h3 className="text-xl font-bold text-gray-900 border-b border-gray-100 pb-3">{tiles.length > 0 ? 'Change Layout' : 'Setup Layout'}</h3>
                {tiles.length > 0 &&
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">Changing
                        the layout will safely move all existing dispensers to the "Replaced Dispensers" section and
                        keep all ingredients.</div>}
                <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">Layout Type</label>
                    <select
                        className="w-full border-gray-300 rounded-md border p-2.5 focus:ring-gray-500 focus:border-gray-500"
                        value={tempLayoutType || ''} onChange={(e) => {
                        const v = e.target.value as LayoutType;
                        setTempLayoutType(v);
                        if (v === 'line') setTempDimensions(d => ({...d, height: 1}));
                        if (v === 'double_line') setTempDimensions(d => ({...d, height: 2}));
                        if (v === 'ring' || v === 'square') setTempDimensions(d => ({...d, height: d.width}));
                    }} required>
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
                            {tempLayoutType === 'ring' || tempLayoutType === 'square' ? 'Size' : 'Width'}
                        </label>
                        <input type="number" min="1" max="100" value={tempDimensions.width} onChange={(e) => {
                            const val = parseInt(e.target.value) || 1;
                            setTempDimensions(d => ({
                                ...d,
                                width: val,
                                height: (tempLayoutType === 'ring' || tempLayoutType === 'square') ? val : d.height
                            }));
                        }}
                               className="w-full border-gray-300 rounded-md border p-2.5 focus:ring-gray-500 focus:border-gray-500"
                               required/>
                    </div>
                    {tempLayoutType !== 'ring' && tempLayoutType !== 'square' && (
                        <div className="flex-1">
                            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Height</label>
                            <input type="number" min="1" max="100" value={tempDimensions.height}
                                   onChange={(e) => setTempDimensions(d => ({
                                       ...d,
                                       height: parseInt(e.target.value) || 1
                                   }))}
                                   className="w-full border-gray-300 rounded-md border p-2.5 disabled:bg-gray-100 focus:ring-gray-500 focus:border-gray-500"
                                   disabled={tempLayoutType === 'line' || tempLayoutType === 'double_line'} required/>
                        </div>
                    )}
                </div>
                <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                    <button type="button" onClick={handleCancelSetup}
                            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium">Cancel
                    </button>
                    <button type="submit"
                            className="px-5 py-2 bg-black text-white rounded-md hover:bg-black font-medium shadow-sm">Confirm
                        Setup
                    </button>
                </div>
            </form>
        </div>
    );

    if (state.mode === 'empty') {
        return (
            <div className="h-full flex items-center justify-center gap-6 relative">
                <button onClick={() => setIsSelectModalOpen(true)}
                        className="px-8 py-4 bg-white border border-gray-300 text-gray-700 rounded-lg shadow-sm hover:bg-gray-50 font-medium text-lg transition-colors">Select
                    Existing
                </button>
                <button type="button" onClick={() => fileInputRef.current?.click()}
                        className="px-8 py-4 bg-white border border-gray-300 text-gray-700 rounded-lg shadow-sm hover:bg-gray-50 font-medium text-lg transition-colors">Load from File
                </button>
                <button onClick={handleCreateNew}
                        className="px-8 py-4 bg-gray-900 border border-gray-900 text-white rounded-lg shadow-sm hover:bg-black font-medium text-lg transition-colors">Create
                    New
                </button>
                <input type="file" accept=".json" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
                <LayoutSelectModal
                    isOpen={isSelectModalOpen}
                    onClose={() => setIsSelectModalOpen(false)}
                    onSelect={(id, data) => {
                        setState(() => ({
                            mode: 'existing',
                            id,
                            data: data as unknown as LayoutSingleCreateRequestDTO,
                            isValidated: true,
                            isValidating: false
                        }));
                        setIsSelectModalOpen(false);
                    }}
                />
                {configModal}
            </div>
        );
    }

    const counts = tiles.reduce((acc, tile) => {
        acc[tile.type]++;
        return acc;
    }, {empty: 0, interface: 0, blocked: 0, dispenser: 0, mixer: 0, capper: 0});

    let editTile: TileDTO | undefined;
    let updateEditTile: ((newTypes: string[]) => void) | undefined;
    let closeEditModal: (() => void) | undefined;

    if (editingDispenser) {
        editTile = tiles.find(t => t.x === editingDispenser.x && t.y === editingDispenser.y);
        updateEditTile = (newTypes) => updateTile(editingDispenser.x, editingDispenser.y, {dispensed_types: newTypes});
        closeEditModal = () => setEditingDispenser(null);
    } else if (editingOrphanIndex !== null) {
        editTile = orphanDispensers[editingOrphanIndex];
        updateEditTile = (newTypes) => setOrphanDispensers(prev => prev.map((o, idx) => idx === editingOrphanIndex ? {
            ...o,
            dispensed_types: newTypes
        } : o));
        closeEditModal = () => setEditingOrphanIndex(null);
    }

    return (
        <div className="h-full flex flex-col p-6 relative">
            {state.mode === 'existing' && (
                <div
                    className="mx-auto mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800 text-center shadow-sm w-full max-w-4xl shrink-0">
                    Using existing Layout. Modifying ingredient list or grid will detach it and create a new draft.
                </div>
            )}

            {validationErrors.length > 0 && (
                <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-md relative shrink-0 shadow-sm w-full">
                    <button type="button" onClick={() => setValidationErrors([])}
                            className="absolute top-2 right-2 text-red-400 hover:text-red-600">✕
                    </button>
                    <h4 className="text-sm font-semibold text-red-800 mb-1">Validation Errors:</h4>
                    <ul className="text-sm text-red-700 list-disc pl-5">{validationErrors.map((err, i) => <li
                        key={i}>{err}</li>)}</ul>
                </div>
            )}

            <form id="layout-tab-form" onSubmit={handleValidate} className="hidden"></form>

            <div className="flex-1 flex gap-6 min-h-0">
                {/* Left Side */}
                <div className="w-52 flex flex-col gap-4 shrink-0 h-full">
                    <div
                        className="bg-white border border-gray-200 rounded-md shadow-sm p-4 flex flex-col gap-4 shrink-0">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Name</label>
                            <input type="text" value={currentData.name || ''}
                                   onChange={(e) => updateData({name: e.target.value})} placeholder="Layout name..."
                                   className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-gray-500 focus:border-gray-500"/>
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Layout Type</label>
                            <div
                                className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded px-2 py-1.5">
                                <span
                                    className="text-sm font-medium text-gray-700 uppercase tracking-wide">{currentData.type?.replace('_', ' ')}</span>
                                <button type="button" onClick={() => {
                                    setTempLayoutType(currentData.type);
                                    setTempDimensions(renderDimensions);
                                    setIsConfiguring(true);
                                }}
                                        className="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors">
                                    <PencilSquareIcon className="w-4 h-4"/></button>
                            </div>
                        </div>
                    </div>

                    <div
                        className="flex flex-col flex-1 min-h-0 bg-white border border-gray-200 rounded-md shadow-sm overflow-hidden">
                        <div className="p-3 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
                            <span className="font-semibold text-sm text-gray-800">Ingredients</span>
                            <div className="flex gap-1">
                                <button type="button" onClick={() => setIsIngListSelectModalOpen(true)}
                                        className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors">
                                    <MagnifyingGlassIcon className="w-4 h-4"/></button>
                                <button type="button" onClick={() => setIsIngListDraftModalOpen(true)}
                                        className="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors">
                                    <PencilSquareIcon className="w-4 h-4"/></button>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Remove ingredient list?")) updateData({
                                        ingredient_list_id: null,
                                        ingredient_list: null
                                    })
                                }} disabled={!currentData.ingredient_list && !currentData.ingredient_list_id}
                                        className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-30">
                                    <TrashIcon className="w-4 h-4"/></button>
                            </div>
                        </div>
                        <div
                            className="bg-white border-b border-gray-100 p-2 text-xs font-medium text-center text-gray-600 truncate">
                            {currentData.ingredient_list ? `${currentData.ingredient_list.name || 'Unnamed'} (Draft)` : fullSelectedList?.name ? fullSelectedList.name : 'No list selected'}
                        </div>
                        <div className="flex-1 overflow-y-auto p-2 space-y-1">
                            {availableIngredients.map(t => (
                                <div key={t} draggable onDragStart={(e) => {
                                    e.dataTransfer.setData('type', 'dispensedType');
                                    e.dataTransfer.setData('payload', JSON.stringify({name: t}));
                                }} onMouseEnter={() => setHoveredType(t)} onMouseLeave={() => setHoveredType(null)}
                                     className="flex items-center justify-between p-2.5 bg-gray-50 border border-gray-200 rounded text-sm cursor-grab active:cursor-grabbing hover:bg-gray-100 transition-colors">
                                    <span className="truncate flex-1 font-medium text-gray-700" title={t}>{t}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Middle Grid */}
                <div
                    className="flex-1 flex flex-col bg-white border border-gray-200 rounded-md shadow-sm relative overflow-hidden">
                    <div
                        className="absolute top-3 right-3 z-20 flex items-center bg-white border border-gray-200 rounded-md shadow-sm opacity-90 hover:opacity-100 transition-opacity">
                        <button type="button" onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}
                                className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-l-md">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4"/>
                            </svg>
                        </button>
                        <span
                            className="px-2 text-xs font-medium text-gray-600 border-x border-gray-200 w-12 text-center">{Math.round(zoom * 100)}%</span>
                        <button type="button" onClick={() => setZoom(z => Math.min(2.5, z + 0.1))}
                                className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-r-md">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/>
                            </svg>
                        </button>
                    </div>

                    <div ref={gridContainerRef} className="flex-1 overflow-auto p-4 flex bg-gray-50/50 relative">
                        <div className="m-auto">
                            <div className="grid gap-1 relative" style={{
                                gridTemplateColumns: `repeat(${renderDimensions.width}, ${80 * zoom}px)`,
                                gridTemplateRows: `repeat(${renderDimensions.height}, ${80 * zoom}px)`
                            }}>
                                {tiles.map((tile) => {
                                    const isHighlighted = hoveredType && tile.type === 'dispenser' && (tile.dispensed_types || []).includes(hoveredType);
                                    return (
                                        <div key={`${tile.x}-${tile.y}`}
                                             className={`w-full h-full border flex flex-col items-center justify-center relative select-none transition-colors ${tile.type === 'empty' ? 'bg-white border-gray-300 hover:bg-gray-100 text-gray-300' : ''} ${tile.type === 'blocked' ? 'bg-gray-800 border-gray-900 text-white' : ''} ${tile.type === 'interface' ? 'bg-blue-50 border-blue-300 text-blue-600 shadow-sm' : ''} ${tile.type === 'mixer' ? 'bg-green-50 border-green-300 text-green-600 shadow-sm' : ''} ${tile.type === 'capper' ? 'bg-red-50 border-red-300 text-red-600 shadow-sm' : ''} ${tile.type === 'dispenser' ? (isHighlighted ? 'bg-green-100 border-green-500 text-green-700 shadow-md ring-2 ring-green-300' : 'bg-orange-50 border-orange-300 text-orange-600 shadow-sm') : ''}`}
                                             draggable={tile.type !== 'blocked'} onDragStart={(e) => {
                                            e.dataTransfer.setData('type', 'gridTile');
                                            e.dataTransfer.setData('payload', JSON.stringify({x: tile.x, y: tile.y}));
                                        }} onDragOver={(e) => e.preventDefault()}
                                             onDrop={(e) => handleDrop(e, tile.x, tile.y)} onClick={() => {
                                            if (tile.type === 'empty') setActiveTileSelect({x: tile.x, y: tile.y});
                                        }}>
                                            {tile.type === 'empty' && <PlusCircleIcon className="w-[45%] h-[45%]"/>}
                                            {tile.type === 'blocked' && <XCircleIcon className="w-[45%] h-[45%]"/>}
                                            {tile.type === 'interface' && <TruckIcon className="w-[45%] h-[45%]"/>}
                                            {tile.type === 'mixer' && <ArrowPathIcon className="w-[45%] h-[45%]"/>}
                                            {tile.type === 'capper' && <CircleStackIcon className="w-[45%] h-[45%]"/>}
                                            {tile.type === 'dispenser' && (
                                                <>
                                                    {(tile.dispensed_types?.length > 0) && (
                                                        <div
                                                            className="absolute left-0 right-0 z-10 flex justify-center pointer-events-none"
                                                            style={{top: `${4 * zoom}px`, padding: `0 ${4 * zoom}px`}}>
                                                            <span
                                                                className="font-bold text-orange-800 bg-white/90 border border-orange-200 rounded shadow-sm truncate leading-none"
                                                                style={{
                                                                    fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                    padding: `${zoom}px ${4 * zoom}px`,
                                                                    borderWidth: `${Math.max(1, zoom)}px`
                                                                }}>{getDispenserInitials(tile.dispensed_types)}</span>
                                                        </div>
                                                    )}
                                                    <FunnelIcon className="w-[45%] h-[45%] z-0"/>
                                                    <div
                                                        className="absolute left-1/2 -translate-x-1/2 z-10 flex items-center justify-center pointer-events-none"
                                                        style={{bottom: `${4 * zoom}px`}}>
                                                        <span
                                                            className="font-bold text-orange-900 bg-orange-100 border border-orange-300 text-center rounded shadow-sm leading-none tracking-tighter"
                                                            style={{
                                                                fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                padding: `${zoom}px`,
                                                                minWidth: `${16 * zoom}px`,
                                                                borderWidth: `${Math.max(1, zoom)}px`
                                                            }}>{tile.dispensed_types?.length > 99 ? '99+' : (tile.dispensed_types?.length || 0)}</span>
                                                    </div>
                                                </>
                                            )}
                                            {(['interface', 'mixer', 'capper'].includes(tile.type) || (tile.type === 'blocked' && currentData.type === 'custom')) && zoom > 0.4 && (
                                                <button type="button"
                                                        className="absolute bottom-1 right-1 z-20 text-xs bg-white text-gray-500 rounded-full w-5 h-5 flex items-center justify-center border hover:text-red-500 hover:border-red-500 hover:bg-red-50 shadow-sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            updateTile(tile.x, tile.y, {type: 'empty'});
                                                        }}><TrashIcon className="w-3.5 h-3.5"/></button>
                                            )}
                                            {tile.type === 'dispenser' && zoom > 0.4 && (
                                                <>
                                                    <button type="button"
                                                            className="absolute bottom-1 right-1 z-20 text-xs bg-white text-gray-500 rounded-full w-5 h-5 flex items-center justify-center border hover:text-red-500 hover:border-red-500 hover:bg-red-50 shadow-sm"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                updateTile(tile.x, tile.y, {
                                                                    type: 'empty',
                                                                    dispensed_types: []
                                                                });
                                                            }}><TrashIcon className="w-3.5 h-3.5"/></button>
                                                    <button type="button"
                                                            className="absolute bottom-1 left-1 z-20 text-xs bg-white text-gray-500 rounded w-5 h-5 flex items-center justify-center border hover:text-blue-600 hover:border-blue-500 hover:bg-blue-50 shadow-sm"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setEditingDispenser({x: tile.x, y: tile.y});
                                                            }}><PencilSquareIcon className="w-3.5 h-3.5"/></button>
                                                </>
                                            )}
                                            {activeTileSelect?.x === tile.x && activeTileSelect?.y === tile.y && (
                                                <div
                                                    className={`absolute z-50 bg-white border border-gray-200 shadow-xl rounded-md flex gap-1.5 p-2 ${
                                                        tile.y >= renderDimensions.height / 2 ? 'bottom-full mb-2' : 'top-full mt-2'
                                                    } ${
                                                        tile.x === 0 ? 'left-0' : tile.x === renderDimensions.width - 1 ? 'right-0' : 'left-1/2 -translate-x-1/2'
                                                    }`}>
                                                    <button type="button"
                                                            className="p-2 hover:bg-blue-50 text-blue-600 rounded-md"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                updateTile(tile.x, tile.y, {type: 'interface'});
                                                                setActiveTileSelect(null);
                                                            }}><TruckIcon className="w-6 h-6"/></button>
                                                    <button type="button"
                                                            className="p-2 hover:bg-orange-50 text-orange-600 rounded-md"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                updateTile(tile.x, tile.y, {
                                                                    type: 'dispenser',
                                                                    dispensed_types: []
                                                                });
                                                                setActiveTileSelect(null);
                                                            }}><FunnelIcon className="w-6 h-6"/></button>
                                                    <button type="button"
                                                            className="p-2 hover:bg-green-50 text-green-600 rounded-md"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                updateTile(tile.x, tile.y, {type: 'mixer'});
                                                                setActiveTileSelect(null);
                                                            }}><ArrowPathIcon className="w-6 h-6"/></button>
                                                    <button type="button"
                                                            className="p-2 hover:bg-red-50 text-red-600 rounded-md"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                updateTile(tile.x, tile.y, {type: 'capper'});
                                                                setActiveTileSelect(null);
                                                            }}><CircleStackIcon className="w-6 h-6"/></button>
                                                    {currentData.type === 'custom' && (
                                                        <button type="button"
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
                        onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
                        e.preventDefault();
                        const t = e.dataTransfer.getData('type');
                        if (t === 'gridTile') {
                            const p = JSON.parse(e.dataTransfer.getData('payload'));
                            const s = tiles.find(x => x.x === p.x && x.y === p.y);
                            if (s && s.type === 'dispenser') {
                                setOrphanDispensers(prev => [...prev, {...s, x: -1, y: -1}]);
                                updateTile(p.x, p.y, {type: 'empty', dispensed_types: []});
                            }
                        }
                    }}>
                        <div className="p-3 border-b border-gray-200 bg-gray-50 flex flex-col gap-2">
                            <span className="font-semibold text-sm text-gray-800">Replaced Dispensers</span>
                            <button type="button" onClick={() => {
                                setOrphanDispensers(prev => [...prev, ...tiles.filter(t => t.type === 'dispenser')]);
                                updateData({
                                    tiles: tiles.map(t => (t.type === 'empty' || (t.type === 'blocked' && currentData.type !== 'custom') ? t : {
                                        ...t,
                                        type: 'empty',
                                        dispensed_types: []
                                    }))
                                });
                            }}
                                    className="w-full px-2 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded hover:bg-red-50 hover:text-red-600 hover:border-red-300 transition-colors">Clear
                                Grid
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50/50">
                            {orphanDispensers.length === 0 &&
                                <p className="text-xs text-gray-400 text-center mt-4">Drag dispensers here to put them
                                    aside.</p>}
                            {orphanDispensers.map((orphan, i) => {
                                const count = orphan.dispensed_types?.length || 0;
                                const initials = count > 0 ? getDispenserInitials(orphan.dispensed_types) : '';
                                const isHighlighted = hoveredType && orphan.dispensed_types.includes(hoveredType);
                                return (
                                    <div key={i} draggable onDragStart={(e) => {
                                        e.dataTransfer.setData('type', 'orphan');
                                        e.dataTransfer.setData('payload', JSON.stringify({index: i}));
                                    }} onDragOver={(e) => e.preventDefault()} onDrop={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        const t = e.dataTransfer.getData('type');
                                        if (t === 'dispensedType') {
                                            const p = JSON.parse(e.dataTransfer.getData('payload'));
                                            setOrphanDispensers(prev => prev.map((o, idx) => (idx === i && !o.dispensed_types.includes(p.name)) ? {
                                                ...o,
                                                dispensed_types: [...o.dispensed_types, p.name]
                                            } : o));
                                        }
                                    }}
                                         className={`w-full border rounded-md flex flex-col items-center justify-center p-3 cursor-grab active:cursor-grabbing transition-all group relative ${isHighlighted ? 'bg-green-100 border-green-500 shadow-md ring-2 ring-green-300' : 'bg-white border-orange-200 shadow-sm hover:border-orange-400 hover:shadow'}`}
                                         title={orphan.dispensed_types.join('\n')}>
                                        <button type="button" onClick={(e) => {
                                            e.stopPropagation();
                                            setEditingOrphanIndex(i);
                                        }}
                                                className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-600 p-1">
                                            <PencilSquareIcon className="w-3.5 h-3.5"/></button>
                                        <FunnelIcon
                                            className={`w-7 h-7 mb-2 ${isHighlighted ? 'text-green-700' : 'text-orange-500'}`}/>
                                        <span
                                            className={`text-[11px] font-medium px-2 py-0.5 rounded-full truncate max-w-full text-center ${isHighlighted ? 'text-green-800 bg-green-200' : 'text-orange-800 bg-orange-100'}`}>{count > 0 ? (initials ? `${initials} (${count})` : `(${count})`) : '(0)'}</span>
                                        <button type="button"
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

            {/* Overlays / Modals */}
            <IngredientListSelectModal isOpen={isIngListSelectModalOpen}
                                       onClose={() => setIsIngListSelectModalOpen(false)} onSelect={(id) => {
                updateData({ingredient_list_id: id, ingredient_list: null});
                setIsIngListSelectModalOpen(false);
            }} onInfo={(id) => setInfoListId(id)}/>
            <IngredientListInfoModal listId={infoListId} onClose={() => setInfoListId(null)}/>
            <LayoutIngredientListDraftModal isOpen={isIngListDraftModalOpen}
                                            initialData={currentData.ingredient_list || fullSelectedList}
                                            onClose={() => setIsIngListDraftModalOpen(false)}
                                            onSuccessDraft={(payload) => {
                                                updateData({ingredient_list: payload, ingredient_list_id: null});
                                                setIsIngListDraftModalOpen(false);
                                            }}/>

            {configModal}

            {editTile && updateEditTile && closeEditModal && (
                <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px] z-40 flex items-center justify-center">
                    <div className="bg-white p-5 rounded-lg shadow-xl border border-gray-200 w-80">
                        <h4 className="font-bold text-gray-800 mb-4 border-b border-gray-100 pb-2">Edit Ingredients</h4>
                        <div className="space-y-2 max-h-56 overflow-y-auto mb-5 pr-1">
                            {editTile.dispensed_types.length === 0 ?
                                <p className="text-gray-400 text-sm italic text-center py-2">No types
                                    assigned.</p> : null}
                            {editTile.dispensed_types.map(dt => (
                                <div key={dt}
                                     className="flex justify-between items-center text-sm bg-gray-50 p-2 border border-gray-200 rounded">
                                    <span className="truncate font-medium text-gray-700">{dt}</span>
                                    <button type="button"
                                            onClick={() => updateEditTile!(editTile!.dispensed_types.filter(t => t !== dt))}
                                            className="text-red-500 hover:bg-red-50 p-1 rounded">✕
                                    </button>
                                </div>
                            ))}
                        </div>
                        <button type="button" onClick={closeEditModal}
                                className="w-full bg-gray-800 hover:bg-gray-700 text-white rounded-md py-2 font-medium">Done
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
});

export default ExperimentLayoutTab;