import {type ChangeEvent, type SyntheticEvent, useEffect, useRef, useState} from 'react';
import {useSearchParams} from 'react-router-dom';
import {useMutation, useQueryClient} from '@tanstack/react-query';
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
import {createOrderList} from '../../api/order_lists';
import type {OrderListCreateRequestDTO, OrderListSingleGetResponseDTO, OrderListType} from '../../types/order_lists';
import {formatName} from '../../utils/formatters';

interface OrderListCreateModalProps {
    isOpen: boolean;
    initialData?: OrderListSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

interface UIItem {
    id: string;
    name: string;
    quantity: number | string;
}

interface UIOrder {
    id: string;
    t_max: number | '';
    items: UIItem[];
}

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

const generateId = () => Math.random().toString(36).substring(2, 9);
const getInitialOrderState = (): UIOrder[] => [{
    id: generateId(),
    t_max: '',
    items: [{id: generateId(), name: '', quantity: 1}]
}];

interface SortableItemProps {
    id: string;
    orderId: string;
    item: UIItem;
    type: OrderListType;
    isOnlyOne: boolean;
    onRemove: (orderId: string, itemId: string) => void;
    onChange: (orderId: string, itemId: string, field: 'name' | 'quantity', value: string | number) => void;
}

function SortableOrderItem({id, orderId, item, type, isOnlyOne, onRemove, onChange}: SortableItemProps) {
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
                        className={`w-full px-3 py-2 border rounded-md bg-gray-50 text-sm flex items-center gap-2 font-semibold min-h-[38px] ${isMixer ? 'text-green-700 border-green-700' : 'text-red-700 border-red-700'}`}>
                        {isMixer ? <ArrowPathIcon className="w-4 h-4"/> : <CircleStackIcon className="w-4 h-4"/>}
                        {isMixer ? 'Mixer' : 'Capper'}
                    </div>
                ) : (
                    <input required type="text" value={item.name}
                           onChange={(e) => onChange(orderId, item.id, 'name', e.target.value)}
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
                        onChange={(e) => onChange(orderId, item.id, 'quantity', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md text-sm border-gray-300 focus:ring-gray-500"
                        autoComplete="none"
                    />
                </div>
            )}

            <div className={`${isSpecial ? '' : 'pt-6'}`}>
                <button type="button" onClick={() => onRemove(orderId, item.id)} disabled={isOnlyOne}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-400"
                        title="Remove Item">
                    <TrashIcon className="w-5 h-5"/>
                </button>
            </div>
        </div>
    );
}

export default function OrderListCreateModal({
                                                 isOpen,
                                                 initialData,
                                                 onClose,
                                                 onSuccessSubmit
                                             }: OrderListCreateModalProps) {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    const [name, setName] = useState('');
    const [type, setType] = useState<OrderListType>('medicine');
    const [orders, setOrders] = useState<UIOrder[]>(getInitialOrderState);
    const [lastCopiedId, setLastCopiedId] = useState<number | null>(null);

    const sensors = useSensors(
        useSensor(PointerSensor, {activationConstraint: {distance: 5}}),
        useSensor(KeyboardSensor, {coordinateGetter: sortableKeyboardCoordinates})
    );

    if (initialData && initialData.id !== lastCopiedId) {
        setLastCopiedId(initialData.id);
        setName(initialData.name ? `${initialData.name} (Copy)` : 'Copy');
        setType(initialData.type);

        if (initialData.orders && initialData.orders.length > 0) {
            setOrders(initialData.orders.map(o => ({
                id: generateId(),
                t_max: o.t_max ?? '',
                items: o.items.map(i => ({id: generateId(), name: i.name || '', quantity: i.quantity || 1}))
            })));
        } else {
            setOrders(getInitialOrderState());
        }
    }

    const resetState = () => {
        setName('');
        setType('medicine');
        setOrders(getInitialOrderState());
        setValidationErrors([]);
        setLastCopiedId(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const mutation = useMutation({
        mutationFn: async (data: OrderListCreateRequestDTO) => {
            setValidationErrors([]);
            await createOrderList(data, true);
            return await createOrderList(data, false);
        },
        onSuccess: async (createdData) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['order_lists']}),
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

    const handleAddOrder = () => setOrders(prev => [...prev, {
        id: generateId(),
        t_max: '',
        items: [{id: generateId(), name: '', quantity: 1}]
    }]);
    const handleOrderChange = (orderId: string, field: 't_max', value: number | '') => setOrders(prev => prev.map(order => order.id === orderId ? {
        ...order,
        [field]: value
    } : order));
    const handleAddItem = (orderId: string) => setOrders(prev => prev.map(order => order.id === orderId ? {
        ...order,
        items: [...order.items, {id: generateId(), name: '', quantity: 1}]
    } : order));
    const handleRemoveItem = (orderId: string, itemId: string) => setOrders(prev => prev.map(order => order.id === orderId ? {
        ...order,
        items: order.items.filter(item => item.id !== itemId)
    } : order).filter(order => order.items.length > 0));
    const handleItemChange = (orderId: string, itemId: string, field: 'name' | 'quantity', value: string | number) => setOrders(prev => prev.map(order => order.id === orderId ? {
        ...order,
        items: order.items.map(item => item.id === itemId ? {...item, [field]: value} : item)
    } : order));

    const addSpecialItem = (orderId: string, specialType: 'mixer' | 'capper') => {
        setOrders(prev => prev.map(order => order.id === orderId ? {
            ...order,
            items: [...order.items, {id: generateId(), name: specialType, quantity: 0}]
        } : order));
    };

    const handleDragEnd = (orderId: string, event: DragEndEvent) => {
        const {active, over} = event;
        if (over && active.id !== over.id) {
            setOrders((prev) => prev.map(order => {
                if (order.id !== orderId) return order;
                const oldIndex = order.items.findIndex(i => i.id === active.id);
                const newIndex = order.items.findIndex(i => i.id === over.id);
                return {...order, items: arrayMove(order.items, oldIndex, newIndex)};
            }));
        }
    };

    const [searchParams, setSearchParams] = useSearchParams();

    useEffect(() => {
        if (isOpen && searchParams.get('upload') === 'true') {
            const nextParams = new URLSearchParams(searchParams);
            nextParams.delete('upload');
            setSearchParams(nextParams, {replace: true});
            setTimeout(() => {
                fileInputRef.current?.click();
            }, 50);
        }
    }, [isOpen, searchParams, setSearchParams]);

    const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = (event.target?.result as string || '').trim();
            try {
                const isCsv = file.name.toLowerCase().endsWith('.csv') || (!text.startsWith('{') && !text.startsWith('['));
                let parsedOrders: UIOrder[] = [];

                if (isCsv) {
                    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
                    if (lines.length < 2) {
                        setValidationErrors(["CSV file is empty or missing data rows."]);
                        if (fileInputRef.current) fileInputRef.current.value = '';
                        return;
                    }

                    const header = lines[0].toLowerCase();
                    const sep = header.includes(';') ? ';' : ',';
                    const headerCols = lines[0].split(sep).map(c => c.trim().toLowerCase());

                    const drugIdx = headerCols.findIndex(c => c.includes('drug') || c.includes('item') || c.includes('name'));
                    const dosageIdx = headerCols.findIndex(c => c.includes('dosage') || c.includes('qty') || c.includes('quantity') || c.includes('amount'));

                    for (let i = 1; i < lines.length; i++) {
                        const row = lines[i].split(sep).map(c => c.trim());
                        if (!row || row.length === 0 || row.every(c => !c)) continue;

                        const rawDrugs = drugIdx !== -1 ? row[drugIdx] : row[1];
                        const rawDosages = dosageIdx !== -1 ? row[dosageIdx] : row[2];
                        if (!rawDrugs) continue;

                        const drugsMatch = rawDrugs.match(/['"]([^'"]+)['"]/g);
                        const cleanDrugs = drugsMatch
                            ? drugsMatch.map(d => d.replace(/['"]/g, '').trim())
                            : rawDrugs.replace(/^\[|\]$/g, '').split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);

                        const dosagesMatch = rawDosages ? rawDosages.match(/\d+(\.\d+)?/g) : null;
                        const cleanDosages = dosagesMatch
                            ? dosagesMatch.map(Number)
                            : (rawDosages ? rawDosages.replace(/^\[|\]$/g, '').split(',').map(s => parseFloat(s.trim()) || 1) : []);

                        const items = cleanDrugs.map((itemDrug, idx) => ({
                            id: generateId(),
                            name: itemDrug,
                            quantity: cleanDosages[idx] !== undefined ? cleanDosages[idx] : 1
                        }));

                        if (items.length > 0) {
                            parsedOrders.push({
                                id: generateId(),
                                t_max: '',
                                items
                            });
                        }
                    }

                    const baseName = file.name.replace(/\.[^/.]+$/, '');
                    setName(baseName || 'orders');
                    setType('medicine');
                } else {
                    const json = JSON.parse(text) as ParsedJSONOrderList;

                    if (!json.orders || !Array.isArray(json.orders)) {
                        setValidationErrors(["Invalid file format. 'orders' array is missing."]);
                        if (fileInputRef.current) fileInputRef.current.value = '';
                        return;
                    }

                    if (json.name) setName(json.name);
                    if (json.type && (json.type === 'medicine' || json.type === 'perfume')) setType(json.type as OrderListType);

                    parsedOrders = json.orders.map((o) => ({
                        id: generateId(),
                        t_max: typeof o.t_max === 'number' ? o.t_max : '',
                        items: (o.items || []).map((i) => ({
                            id: generateId(),
                            name: i.name || '',
                            quantity: typeof i.quantity === 'number' ? i.quantity : 1
                        }))
                    }));
                }

                if (parsedOrders.length === 0) parsedOrders.push({
                    id: generateId(),
                    t_max: '',
                    items: [{id: generateId(), name: '', quantity: 1}]
                });

                setOrders(parsedOrders);
                setValidationErrors([]);
            } catch (err: unknown) {
                const errorMessage = err instanceof Error ? err.message : 'Invalid file format';
                setValidationErrors([`Failed to parse file: ${errorMessage}`]);
            }
            if (fileInputRef.current) fileInputRef.current.value = '';
        };
        reader.readAsText(file);
    };

    const handleSubmit = (e: SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault();
        const finalName = name.trim();

        const payload: OrderListCreateRequestDTO = {
            name: finalName.length >= 1 ? finalName : null,
            type: type,
            orders: orders.map(o => ({
                items: o.items.map(i => {
                    const isSpecial = i.name.toLowerCase() === 'mixer' || i.name.toLowerCase() === 'capper';
                    return {
                        name: i.name.trim().toLowerCase() === 'mixer' ? 'mixer' : i.name.trim().toLowerCase() === 'capper' ? 'capper' : i.name.trim(),
                        quantity: isSpecial ? 0 : Number(i.quantity)
                    };
                }),
                t_max: type === 'perfume' ? Number(o.t_max) : null
            }))
        };

        mutation.mutate(payload);
    };

    const totalItems = orders.reduce((sum, order) => sum + order.items.length, 0);
    const isOnlyOneItemLeft = totalItems === 1;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" onClick={onClose}></div>
            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Create Order List</h2>
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
                        <button type="button" onClick={() => setValidationErrors([])}
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

                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                            <input minLength={1} type="text" name="name" value={name}
                                   onChange={(e) => setName(e.target.value)}
                                   className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"
                                   placeholder="Enter order list name..." autoComplete="none"/>
                        </div>

                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                            <select value={type} onChange={(e) => setType(e.target.value as OrderListType)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 bg-white text-sm">
                                <option value="medicine">Medicine</option>
                                <option value="perfume">Perfume</option>
                            </select>
                        </div>

                        <div className="space-y-6">
                            {orders.map((order, orderIndex) => (
                                <div key={order.id}
                                     className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Order {orderIndex + 1}</h3>

                                    {type === 'perfume' && (
                                        <div className="mb-4 sm:w-1/3">
                                            <label className="block text-xs font-medium text-gray-500 mb-1">T
                                                Max</label>
                                            <input required={type === 'perfume'} type="number" min="0"
                                                   value={order.t_max}
                                                   onChange={(e) => handleOrderChange(order.id, 't_max', e.target.value === '' ? '' : Number(e.target.value))}
                                                   className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"
                                                   placeholder="e.g. 50" autoComplete="none"/>
                                        </div>
                                    )}

                                    <DndContext sensors={sensors} collisionDetection={closestCenter}
                                                onDragEnd={(e) => handleDragEnd(order.id, e)}>
                                        <SortableContext items={order.items.map(i => i.id)}
                                                         strategy={verticalListSortingStrategy}>
                                            <div className="space-y-3">
                                                {order.items.map((item) => (
                                                    <SortableOrderItem
                                                        key={item.id}
                                                        id={item.id}
                                                        orderId={order.id}
                                                        item={item}
                                                        type={type}
                                                        isOnlyOne={isOnlyOneItemLeft}
                                                        onRemove={handleRemoveItem}
                                                        onChange={handleItemChange}
                                                    />
                                                ))}
                                            </div>
                                        </SortableContext>
                                    </DndContext>

                                    <div className="mt-4 flex flex-wrap gap-3">
                                        <button type="button" onClick={() => handleAddItem(order.id)}
                                                className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                            <PlusIcon className="w-4 h-4"/> Add Item
                                        </button>
                                        {type === 'perfume' && (
                                            <>
                                                <button type="button" onClick={() => addSpecialItem(order.id, 'mixer')}
                                                        className="text-sm font-medium text-green-700 hover:text-green-800 flex items-center gap-1">
                                                    <PlusIcon className="w-4 h-4"/> Add Mixer
                                                </button>
                                                <button type="button" onClick={() => addSpecialItem(order.id, 'capper')}
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
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Add Order
                        </button>
                    </div>

                    <div
                        className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-between items-center shrink-0">
                        <div>
                            <input type="file" accept=".json,.csv" ref={fileInputRef} onChange={handleFileUpload}
                                   className="hidden" id="order-file-upload"/>
                            <label htmlFor="order-file-upload"
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
                            <button type="submit" disabled={mutation.isPending}
                                    className="px-4 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center">{mutation.isPending ? 'Validating...' : 'Create Order List'}</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}