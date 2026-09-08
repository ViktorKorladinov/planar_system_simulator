import {type ChangeEvent, forwardRef, type SyntheticEvent, useImperativeHandle, useRef, useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {
    closestCenter,
    DndContext,
    type DragEndEvent,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy
} from '@dnd-kit/sortable';
import {CSS} from '@dnd-kit/utilities';
import {ArrowPathIcon, Bars2Icon, CircleStackIcon, PlusIcon, TrashIcon} from "@heroicons/react/24/outline";

import {createOrderList} from '../../../api/order_lists';
import type {OrderListCreateRequestDTO, OrderListType} from '../../../types/order_lists';
import type {EntityState} from '../ExperimentCreateModal';
import OrderListSelectModal from '../../order_lists/OrderListSelectModal';

interface Props {
    state: EntityState<OrderListCreateRequestDTO>;
    setState: (updater: (prev: EntityState<OrderListCreateRequestDTO>) => EntityState<OrderListCreateRequestDTO>) => void;
}

export interface OrderListTabRef {
    discard: () => void;
    triggerFileUpload: () => void;
    validate: () => Promise<OrderListCreateRequestDTO | null>;
}

const INITIAL_FORM_STATE: OrderListCreateRequestDTO = {
    name: '', type: 'medicine', orders: [{t_max: null, items: [{name: '', quantity: 1}]}]
};

interface ParsedJSONItem {
    name?: string;
    quantity?: number;
}

interface ParsedJSONOrder {
    t_max?: number;
    items?: ParsedJSONItem[];
}

interface ParsedJSONOrderList {
    name?: string;
    type?: string;
    orders?: ParsedJSONOrder[];
}

interface SortableRowProps {
    id: string;
    orderIndex: number;
    itemIndex: number;
    item: { name: string; quantity: number | string };
    type: OrderListType;
    isOnlyOne: boolean;
    onRemove: (oIdx: number, iIdx: number) => void;
    onChange: (oIdx: number, iIdx: number, field: 'name' | 'quantity', value: string | number) => void;
}

function SortableOrderItem({id, orderIndex, itemIndex, item, type, isOnlyOne, onRemove, onChange}: SortableRowProps) {
    const {attributes, listeners, setNodeRef, transform, transition} = useSortable({id});
    const isMixer = item.name.toLowerCase() === 'mixer';
    const isCapper = item.name.toLowerCase() === 'capper';
    const isSpecial = isMixer || isCapper;

    const style = {transform: CSS.Transform.toString(transform), transition};

    return (
        <div ref={setNodeRef} style={style}
             className={`flex ${isSpecial ? 'items-center' : 'items-start'} gap-3 bg-white group p-1 rounded-md z-10 relative`}>
            <div {...attributes} {...listeners}
                 className={`${isSpecial ? '' : 'pt-6'} cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 shrink-0`}>
                <Bars2Icon className="w-5 h-5"/>
            </div>

            <div className="flex-1">
                {!isSpecial && <label className="block text-xs font-medium text-gray-500 mb-1">Item Name</label>}
                {isSpecial ? (
                    <div
                        className={`w-full px-3 py-2 border rounded-md bg-gray-50 text-sm flex items-center gap-2 font-semibold min-h-9.5 ${isMixer ? 'text-green-700 border-green-200' : 'text-red-700 border-red-200'}`}>
                        {isMixer ? <ArrowPathIcon className="w-4 h-4"/> : <CircleStackIcon className="w-4 h-4"/>}
                        {isMixer ? 'Mixer' : 'Capper'}
                    </div>
                ) : (
                    <input required type="text" value={item.name}
                           onChange={(e) => onChange(orderIndex, itemIndex, 'name', e.target.value)}
                           className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 text-sm"
                           placeholder="e.g. Paracetamol" autoComplete="none"/>
                )}
            </div>

            {!isSpecial && (
                <div className="w-32">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Amount</label>
                    <input
                        required
                        type="number"
                        min={type === 'perfume' ? "0.01" : "1"}
                        step={type === 'perfume' ? "any" : "1"}
                        value={item.quantity}
                        onChange={(e) => onChange(orderIndex, itemIndex, 'quantity', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md text-sm border-gray-300 focus:ring-gray-500"
                        autoComplete="none"
                    />
                </div>
            )}

            <div className={`${isSpecial ? '' : 'pt-6'}`}>
                <button type="button" onClick={() => onRemove(orderIndex, itemIndex)} disabled={isOnlyOne}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-400"
                        title="Remove Item">
                    <TrashIcon className="w-5 h-5"/>
                </button>
            </div>
        </div>
    );
}

const ExperimentOrderListTab = forwardRef<OrderListTabRef, Props>(({state, setState}, ref) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [validationErrors, setValidationErrors] = useState<string[]>([]);
    const [isSelectModalOpen, setIsSelectModalOpen] = useState(false);

    const sensors = useSensors(
        useSensor(PointerSensor, {activationConstraint: {distance: 5}}),
        useSensor(KeyboardSensor, {coordinateGetter: sortableKeyboardCoordinates})
    );

    const validateMutation = useMutation({
        mutationFn: async (data: OrderListCreateRequestDTO) => {
            setValidationErrors([]);
            await createOrderList(data, true);
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

    const performValidation = async () => {
        if (!state.data) return null;
        setState(prev => ({...prev, isValidating: true}));

        const payload: OrderListCreateRequestDTO = {
            name: state.data.name?.trim() || (null as unknown as string),
            type: state.data.type,
            orders: state.data.orders.map(o => ({
                items: o.items.map(i => {
                    const isSpecial = i.name.toLowerCase() === 'mixer' || i.name.toLowerCase() === 'capper';
                    return {
                        name: i.name.trim().toLowerCase() === 'mixer' ? 'mixer' : i.name.trim().toLowerCase() === 'capper' ? 'capper' : i.name.trim(),
                        quantity: isSpecial ? 0 : (String(i.quantity) === '' ? ("" as unknown as number) : Number(i.quantity))
                    };
                }),
                t_max: state.data!.type === 'perfume' ? (o.t_max !== null ? Number(o.t_max) : null) : null
            }))
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
            if (fileInputRef.current) fileInputRef.current.value = '';
        },
        triggerFileUpload: () => {
            fileInputRef.current?.click();
        },
        validate: async () => {
            if (state.isValidated && state.data) return state.data as OrderListCreateRequestDTO;
            return await performValidation();
        }
    }));

    const updateData = (updates: Partial<OrderListCreateRequestDTO>) => {
        setState(prev => ({
            ...prev,
            mode: 'draft',
            isValidated: false,
            isValidating: false,
            data: {...(prev.data || INITIAL_FORM_STATE), ...updates}
        }));
    };

    const handleValidate = async (e: SyntheticEvent) => {
        e.preventDefault();
        await performValidation();
    };

    const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const text = event.target?.result as string;
                if (file.name.endsWith('.csv')) {
                    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
                    if (lines.length === 0 || !lines[0].toLowerCase().includes('seqn')) {
                        setValidationErrors(["Invalid CSV format. Missing header."]);
                        return;
                    }
                    
                    const newOrders = [];
                    for (let i = 1; i < lines.length; i++) {
                        const parts = lines[i].split(';');
                        if (parts.length >= 3) {
                            const drugNamesStr = parts[1];
                            const dosagesStr = parts[2];
                            
                            // parse python-like arrays: "['DRUG_A', 'DRUG_B']" -> ["DRUG_A", "DRUG_B"]
                            const drugsMatch = drugNamesStr.match(/'([^']+)'/g);
                            const drugs = drugsMatch ? drugsMatch.map(d => d.replace(/'/g, '')) : [];
                            
                            // parse python-like arrays: "[1, 2]" -> [1, 2]
                            const dosagesMatch = dosagesStr.match(/\d+(\.\d+)?/g);
                            const dosages = dosagesMatch ? dosagesMatch.map(Number) : [];
                            
                            if (drugs.length > 0 && drugs.length === dosages.length) {
                                const items = drugs.map((name, idx) => ({
                                    name,
                                    quantity: dosages[idx]
                                }));
                                newOrders.push({ t_max: null, items });
                            }
                        }
                    }
                    
                    if (newOrders.length === 0) newOrders.push({t_max: null, items: [{name: '', quantity: 1}]});
                    
                    updateData({
                        name: file.name.replace('.csv', ''),
                        orders: newOrders
                    });
                    setValidationErrors([]);
                } else {
                    const json = JSON.parse(text) as ParsedJSONOrderList;
                    if (!json.orders || !Array.isArray(json.orders)) {
                        setValidationErrors(["Invalid file format. 'orders' array is missing."]);
                        return;
                    }

                    const newOrders = json.orders.map((o) => ({
                        t_max: typeof o.t_max === 'number' ? o.t_max : null,
                        items: (o.items || []).map((i) => ({
                            name: i.name || '',
                            quantity: typeof i.quantity === 'number' ? i.quantity : 1
                        }))
                    }));

                    if (newOrders.length === 0) newOrders.push({t_max: null, items: [{name: '', quantity: 1}]});

                    updateData({
                        name: json.name || currentData.name,
                        type: (json.type === 'medicine' || json.type === 'perfume') ? json.type : currentData.type,
                        orders: newOrders
                    });
                    setValidationErrors([]);
                }
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'Failed to parse file';
                setValidationErrors([`Failed to parse file: ${errorMessage}`]);
            }
            if (fileInputRef.current) fileInputRef.current.value = '';
        };
        reader.readAsText(file);
    };

    if (state.mode === 'empty') {
        return (
            <div className="h-full flex items-center justify-center gap-6">
                <button type="button" onClick={() => setIsSelectModalOpen(true)}
                        className="px-8 py-4 bg-white border border-gray-300 text-gray-700 rounded-lg shadow-sm hover:bg-gray-50 font-medium text-lg transition-colors">Select
                    Existing
                </button>
                <button type="button" onClick={() => setState(() => ({
                    mode: 'draft',
                    id: null,
                    data: INITIAL_FORM_STATE,
                    isValidated: false,
                    isValidating: false
                }))}
                        className="px-8 py-4 bg-gray-900 border border-gray-900 text-white rounded-lg shadow-sm hover:bg-black font-medium text-lg transition-colors">Create
                    New
                </button>

                <OrderListSelectModal
                    isOpen={isSelectModalOpen}
                    onClose={() => setIsSelectModalOpen(false)}
                    onSelect={(id, data) => {
                        setState(() => ({
                            mode: 'existing',
                            id,
                            data: data as unknown as OrderListCreateRequestDTO,
                            isValidated: true,
                            isValidating: false
                        }));
                        setIsSelectModalOpen(false);
                    }}
                />

                <input type="file" accept=".json,.csv" ref={fileInputRef} onChange={handleFileUpload} className="hidden"/>
            </div>
        );
    }

    const currentData = state.data || INITIAL_FORM_STATE;
    const totalItems = currentData.orders.reduce((sum, order) => sum + order.items.length, 0);
    const isOnlyOneItemLeft = totalItems === 1;

    const handleDragEnd = (orderIndex: number, event: DragEndEvent) => {
        const {active, over} = event;
        if (over && active.id !== over.id) {
            const newOrders = [...currentData.orders];
            const items = [...newOrders[orderIndex].items];

            const oldIndex = items.findIndex((_, idx) => `item-${orderIndex}-${idx}` === active.id);
            const newIndex = items.findIndex((_, idx) => `item-${orderIndex}-${idx}` === over.id);

            newOrders[orderIndex].items = arrayMove(items, oldIndex, newIndex);
            updateData({orders: newOrders});
        }
    };

    const addSpecialItem = (orderIndex: number, specialType: 'mixer' | 'capper') => {
        const newOrders = [...currentData.orders];
        newOrders[orderIndex].items = [...newOrders[orderIndex].items, {name: specialType, quantity: 0}];
        updateData({orders: newOrders});
    };

    const handleAddOrder = () => updateData({
        orders: [...currentData.orders, {
            t_max: null,
            items: [{name: '', quantity: 1}]
        }]
    });
    const handleOrderChange = (orderIndex: number, field: 't_max', value: number | null) => {
        const newOrders = [...currentData.orders];
        newOrders[orderIndex] = {...newOrders[orderIndex], [field]: value};
        updateData({orders: newOrders});
    };
    const handleAddItem = (orderIndex: number) => {
        const newOrders = [...currentData.orders];
        newOrders[orderIndex] = {
            ...newOrders[orderIndex],
            items: [...newOrders[orderIndex].items, {name: '', quantity: 1}]
        };
        updateData({orders: newOrders});
    };
    const handleRemoveItem = (orderIndex: number, itemIndex: number) => {
        const newOrders = [...currentData.orders];
        newOrders[orderIndex].items = newOrders[orderIndex].items.filter((_, i) => i !== itemIndex);
        updateData({orders: newOrders.filter(o => o.items.length > 0)});
    };
    const handleItemChange = (orderIndex: number, itemIndex: number, field: 'name' | 'quantity', value: string | number) => {
        const newOrders = [...currentData.orders];
        const newItems = [...newOrders[orderIndex].items];
        newItems[itemIndex] = {...newItems[itemIndex], [field]: value};
        newOrders[orderIndex] = {...newOrders[orderIndex], items: newItems};
        updateData({orders: newOrders});
    };

    return (
        <div className="h-full relative overflow-y-auto p-6">
            {state.mode === 'existing' && (
                <div
                    className="max-w-4xl mx-auto mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800 text-center shadow-sm">
                    Using existing Order List. Modifying fields will detach it and create a new draft.
                </div>
            )}

            {validationErrors.length > 0 && (
                <div
                    className="max-w-4xl mx-auto mb-4 p-3 bg-red-50 border border-red-200 rounded-md relative shrink-0 shadow-sm">
                    <button type="button" onClick={() => setValidationErrors([])}
                            className="absolute top-2 right-2 text-red-400 hover:text-red-600">✕
                    </button>
                    <h4 className="text-sm font-semibold text-red-800 mb-1">Validation Errors:</h4>
                    <ul className="text-sm text-red-700 list-disc pl-5">
                        {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                    </ul>
                </div>
            )}

            <form id="order-list-tab-form" onSubmit={handleValidate} className="space-y-6 max-w-4xl mx-auto pb-8">
                <input type="file" accept=".json,.csv" ref={fileInputRef} onChange={handleFileUpload} className="hidden"/>

                <div className="bg-white p-5 rounded-md border border-gray-200 shadow-sm space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                        <input type="text" value={currentData.name || ''}
                               onChange={(e) => updateData({name: e.target.value})}
                               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 text-sm"
                               placeholder="Order list name... (Optional)"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                        <select value={currentData.type}
                                onChange={(e) => updateData({type: e.target.value as OrderListType})}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 bg-white text-sm">
                            <option value="medicine">Medicine</option>
                            <option value="perfume">Perfume</option>
                        </select>
                    </div>
                </div>

                <div className="space-y-6">
                    {currentData.orders.map((order, orderIndex) => (
                        <div key={orderIndex} className="bg-white p-5 rounded-md border border-gray-200 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Order {orderIndex + 1}</h3>

                            {currentData.type === 'perfume' && (
                                <div className="mb-4 sm:w-1/3">
                                    <label className="block text-xs font-medium text-gray-500 mb-1">T Max</label>
                                    <input required={currentData.type === 'perfume'} type="number" min="0"
                                           value={order.t_max ?? ''}
                                           onChange={(e) => handleOrderChange(orderIndex, 't_max', e.target.value === '' ? null : Number(e.target.value))}
                                           className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 text-sm"
                                           placeholder="e.g. 50"/>
                                </div>
                            )}

                            <DndContext sensors={sensors} collisionDetection={closestCenter}
                                        onDragEnd={(e) => handleDragEnd(orderIndex, e)}>
                                <SortableContext items={order.items.map((_, idx) => `item-${orderIndex}-${idx}`)}
                                                 strategy={verticalListSortingStrategy}>
                                    <div className="space-y-3">
                                        {order.items.map((item, itemIndex) => (
                                            <SortableOrderItem
                                                key={`item-${orderIndex}-${itemIndex}`}
                                                id={`item-${orderIndex}-${itemIndex}`}
                                                orderIndex={orderIndex}
                                                itemIndex={itemIndex}
                                                item={item}
                                                type={currentData.type}
                                                isOnlyOne={isOnlyOneItemLeft}
                                                onRemove={handleRemoveItem}
                                                onChange={handleItemChange}
                                            />
                                        ))}
                                    </div>
                                </SortableContext>
                            </DndContext>

                            <div className="mt-4 flex flex-wrap gap-3">
                                <button type="button" onClick={() => handleAddItem(orderIndex)}
                                        className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                    <PlusIcon className="w-4 h-4"/> Add Item
                                </button>
                                {currentData.type === 'perfume' && (
                                    <>
                                        <button type="button" onClick={() => addSpecialItem(orderIndex, 'mixer')}
                                                className="text-sm font-medium text-green-700 hover:text-green-800 flex items-center gap-1">
                                            <PlusIcon className="w-4 h-4"/> Add Mixer
                                        </button>
                                        <button type="button" onClick={() => addSpecialItem(orderIndex, 'capper')}
                                                className="text-sm font-medium text-red-700 hover:text-red-800 flex items-center gap-1">
                                            <PlusIcon className="w-4 h-4"/> Add Capper
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <button type="button" onClick={handleAddOrder}
                        className="w-full py-3 border-2 border-dashed border-gray-300 rounded-md text-gray-600 font-medium hover:bg-gray-50 hover:border-gray-400 transition-colors flex items-center justify-center gap-2">
                    <PlusIcon className="w-5 h-5"/> Add Order
                </button>
            </form>
        </div>
    );
});

export default ExperimentOrderListTab;