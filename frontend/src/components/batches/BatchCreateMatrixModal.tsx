import {type SyntheticEvent, useRef, useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createBatchMatrix} from '../../api/batches';
import ExperimentConfigurationTab, {type ConfigTabRef} from '../experiments/tabs/ExperimentConfigurationTab';
import ExperimentLayoutTab, {type LayoutTabRef} from "../experiments/tabs/ExperimentLayoutTab";
import ExperimentOrderListTab, {type OrderListTabRef} from '../experiments/tabs/ExperimentOrderListTab';
import type {EntityState} from '../experiments/ExperimentCreateModal';
import {
    ArrowUpTrayIcon,
    CheckBadgeIcon,
    CheckIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    ExclamationTriangleIcon,
    TrashIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';
import type {ExperimentMatrixCreateRequestDTO} from "../../types/batches";
import type {ConfigurationDTO, ConfigurationSingleCreateRequestDTO} from "../../types/configurations";
import type {LayoutDTO, LayoutSingleCreateRequestDTO} from "../../types/layouts";
import type {OrderListCreateRequestDTO, OrderListDTO} from "../../types/order_lists";

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

// Helper to create blank entity states
const createDefaultEntityState = <T, >(mode: 'existing' | 'draft' | 'empty' = 'empty'): EntityState<T> => ({
    mode: mode, id: null, data: null, isValidated: false
});

function formatDuration(totalSeconds: number): string {
    const days = Math.floor(totalSeconds / (3600 * 24));
    const hours = Math.floor((totalSeconds % (3600 * 24)) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const parts = [];
    if (days > 0) parts.push(`${days} d`);
    if (hours > 0) parts.push(`${hours} h`);
    if (minutes > 0) parts.push(`${minutes} m`);
    if (seconds > 0 || parts.length === 0) parts.push(`${seconds} s`);

    return parts.join(' ');
}

export default function BatchMatrixModal({isOpen, onClose, onSuccessSubmit}: Props) {
    const queryClient = useQueryClient();

    const [batchName, setBatchName] = useState('');

    // Distinct state per entity type
    const [configurations, setConfigurations] = useState<EntityState<ConfigurationSingleCreateRequestDTO>[]>([createDefaultEntityState('empty')]);
    const [layouts, setLayouts] = useState<EntityState<LayoutSingleCreateRequestDTO>[]>([createDefaultEntityState('empty')]);
    const [orderLists, setOrderLists] = useState<EntityState<OrderListCreateRequestDTO>[]>([createDefaultEntityState('empty')]);

    // Track standard indexes separately for pagination
    const [activeTab, setActiveTab] = useState<'configuration' | 'layout' | 'order_list'>('configuration');
    const [configIndex, setConfigIndex] = useState(0);
    const [layoutIndex, setLayoutIndex] = useState(0);
    const [orderListIndex, setOrderListIndex] = useState(0);

    const [batchError, setBatchError] = useState<string | null>(null);
    const [submitWarning, setSubmitWarning] = useState<string | null>(null);
    const [isGlobalSubmitting, setIsGlobalSubmitting] = useState(false);

    // Submission Confirmation State including warnings/errors
    const [confirmModalData, setConfirmModalData] = useState<{
        amount: number,
        duration: number,
        skipped: number,
        warnings: string[] | null,
        payload: ExperimentMatrixCreateRequestDTO
    } | null>(null);

    // Standard refs for individual entity validation
    const configTabRef = useRef<ConfigTabRef>(null);
    const layoutTabRef = useRef<LayoutTabRef>(null);
    const orderListTabRef = useRef<OrderListTabRef>(null);

    // Current explicit entities
    const currentConfig = configurations[configIndex];
    const currentLayout = layouts[layoutIndex];
    const currentOrderList = orderLists[orderListIndex];

    // Explicit Type-Safe Updaters
    const handleConfigChange = (updater: (prev: EntityState<ConfigurationSingleCreateRequestDTO>) => EntityState<ConfigurationSingleCreateRequestDTO>) => {
        setSubmitWarning(null);
        setConfigurations(prev => prev.map((ent, i) => i === configIndex ? updater(ent) : ent));
    };

    const handleLayoutChange = (updater: (prev: EntityState<LayoutSingleCreateRequestDTO>) => EntityState<LayoutSingleCreateRequestDTO>) => {
        setSubmitWarning(null);
        setLayouts(prev => prev.map((ent, i) => i === layoutIndex ? updater(ent) : ent));
    };

    const handleOrderListChange = (updater: (prev: EntityState<OrderListCreateRequestDTO>) => EntityState<OrderListCreateRequestDTO>) => {
        setSubmitWarning(null);
        setOrderLists(prev => prev.map((ent, i) => i === orderListIndex ? updater(ent) : ent));
    };

    const buildMatrixRequestPayload = (): ExperimentMatrixCreateRequestDTO => {
        const payload: ExperimentMatrixCreateRequestDTO = {
            name: batchName.trim() ? batchName.trim() : (null as unknown as string),
            configuration_ids: [],
            configurations: [],
            layout_ids: [],
            layouts: [],
            order_list_ids: [],
            order_lists: []
        };

        configurations.forEach(ent => {
            if (ent.mode === 'existing' && ent.id) payload.configuration_ids.push(ent.id);
            else if (ent.data) payload.configurations.push(ent.data as unknown as ConfigurationDTO);
        });

        layouts.forEach(ent => {
            if (ent.mode === 'existing' && ent.id) payload.layout_ids.push(ent.id);
            else if (ent.data) {
                const layoutData = ent.data;
                const isDraftIngList = layoutData.ingredient_list && !('id' in layoutData.ingredient_list);
                const layoutPayload = {
                    ...layoutData,
                    ingredient_list_id: isDraftIngList ? null : (layoutData.ingredient_list_id ?? (layoutData.ingredient_list as {
                        id?: number
                    })?.id ?? null),
                    ingredient_list: isDraftIngList ? layoutData.ingredient_list : null,
                    tiles: layoutData.tiles.map(t => ({
                        x: t.x, y: t.y, type: t.type,
                        dispensed_types: t.type === 'dispenser' ? t.dispensed_types : (null as unknown as string[])
                    }))
                };
                payload.layouts.push(layoutPayload as unknown as LayoutDTO);
            }
        });

        orderLists.forEach(ent => {
            if (ent.mode === 'existing' && ent.id) payload.order_list_ids.push(ent.id);
            else if (ent.data) payload.order_lists.push(ent.data as unknown as OrderListDTO);
        });

        return payload;
    };

    const handleAddEntity = () => {
        if (activeTab === 'configuration') {
            setConfigurations(prev => [...prev, createDefaultEntityState('empty')]);
            setConfigIndex(configurations.length);
        } else if (activeTab === 'layout') {
            setLayouts(prev => [...prev, createDefaultEntityState('empty')]);
            setLayoutIndex(layouts.length);
        } else {
            setOrderLists(prev => [...prev, createDefaultEntityState('empty')]);
            setOrderListIndex(orderLists.length);
        }
    };

    const handleRemoveOrResetCurrentEntity = () => {
        const entityName = activeTab.replace('_', ' ');
        if (window.confirm(`Are you sure you want to discard/remove this ${entityName}?`)) {
            if (activeTab === 'configuration') {
                if (configurations.length === 1) {
                    configTabRef.current?.discard();
                } else {
                    setConfigurations(prev => prev.filter((_, i) => i !== configIndex));
                    setConfigIndex(prev => Math.max(0, prev - 1));
                }
            } else if (activeTab === 'layout') {
                if (layouts.length === 1) {
                    layoutTabRef.current?.discard();
                } else {
                    setLayouts(prev => prev.filter((_, i) => i !== layoutIndex));
                    setLayoutIndex(prev => Math.max(0, prev - 1));
                }
            } else {
                if (orderLists.length === 1) {
                    orderListTabRef.current?.discard();
                } else {
                    setOrderLists(prev => prev.filter((_, i) => i !== orderListIndex));
                    setOrderListIndex(prev => Math.max(0, prev - 1));
                }
            }
        }
    };

    const resetEntireMatrix = () => {
        setBatchName('');
        setConfigurations([createDefaultEntityState('empty')]);
        setLayouts([createDefaultEntityState('empty')]);
        setOrderLists([createDefaultEntityState('empty')]);
        setConfigIndex(0);
        setLayoutIndex(0);
        setOrderListIndex(0);
        setActiveTab('configuration');
        setBatchError(null);
        setSubmitWarning(null);
        setConfirmModalData(null);
    };

    const handleDiscardEntireMatrix = () => {
        if (window.confirm("Are you sure you want to discard the entire Batch?")) {
            resetEntireMatrix();
            onClose();
        }
    };

    const createMatrixMutation = useMutation({
        mutationFn: async ({payload, isDryRun}: { payload: ExperimentMatrixCreateRequestDTO, isDryRun: boolean }) => {
            return await createBatchMatrix(payload, isDryRun);
        },
        onSuccess: async (data, variables) => {
            if (variables.isDryRun) {
                if (data.created_amount === 0) {
                    setConfirmModalData(null);
                    setBatchError(data.errors && data.errors.length > 0 ? data.errors.join(' | ') : "Validation failed internally.");
                    return;
                }

                setConfirmModalData({
                    amount: data.created_amount,
                    duration: data.estimated_time,
                    skipped: data.skipped_amount,
                    warnings: (data.created_amount > 0 && data.errors && data.errors.length > 0) ? data.errors : null,
                    payload: variables.payload
                });
            } else {
                await Promise.all([
                    queryClient.invalidateQueries({queryKey: ['batches']}),
                    queryClient.invalidateQueries({queryKey: ['experiments']})
                ]);
                onSuccessSubmit(data.name, data.id);
                resetEntireMatrix();
                onClose();
            }
        },
        onError: (err: unknown) => {
            if (err && typeof err === 'object') {
                const apiError = err as { errors?: string[]; detail?: unknown };
                if (Array.isArray(apiError.errors) && apiError.errors.length > 0) {
                    setBatchError(apiError.errors.join(' | '));
                    return;
                }
                if (apiError.detail) {
                    setBatchError(typeof apiError.detail === 'string' ? apiError.detail : JSON.stringify(apiError.detail));
                    return;
                }
            }
            if (Array.isArray(err)) setBatchError(err.join(' | '));
            else if (typeof err === 'string') setBatchError(err);
            else setBatchError("Validation failed internally.");
        },
        onSettled: () => {
            setIsGlobalSubmitting(false);
        }
    });

    const handleCreateBatchSoftMatrix = (e: SyntheticEvent) => {
        e.preventDefault();
        if (isGlobalSubmitting || createMatrixMutation.isPending) return;

        setBatchError(null);
        setSubmitWarning(null);
        setIsGlobalSubmitting(true);

        const payload = buildMatrixRequestPayload();

        if (payload.configurations.length + payload.configuration_ids.length === 0) {
            setBatchError("Please add or select at least 1 Configuration.");
            setIsGlobalSubmitting(false);
            return;
        }
        if (payload.layouts.length + payload.layout_ids.length === 0) {
            setBatchError("Please add or select at least 1 Layout.");
            setIsGlobalSubmitting(false);
            return;
        }
        if (payload.order_lists.length + payload.order_list_ids.length === 0) {
            setBatchError("Please add or select at least 1 Order List.");
            setIsGlobalSubmitting(false);
            return;
        }

        createMatrixMutation.mutate({payload, isDryRun: true});
    };

    const handleFinalConfirmMatrix = () => {
        if (!confirmModalData) return;
        setIsGlobalSubmitting(true);
        createMatrixMutation.mutate({payload: confirmModalData.payload, isDryRun: false});
    };

    // Header specific variables
    const entityLabel = activeTab === 'configuration' ? 'Configuration' : activeTab === 'layout' ? 'Layout' : 'Order List';
    const currentMode = activeTab === 'configuration' ? currentConfig.mode : activeTab === 'layout' ? currentLayout.mode : currentOrderList.mode;
    const isCurrentValidated = activeTab === 'configuration' ? currentConfig.isValidated : activeTab === 'layout' ? currentLayout.isValidated : currentOrderList.isValidated;
    const formId = activeTab === 'configuration' ? 'config-tab-form' : activeTab === 'layout' ? 'layout-tab-form' : 'order-list-tab-form';

    const isValidateDisabled = activeTab === 'configuration'
        ? (currentConfig.isValidating || currentConfig.isValidated || currentConfig.mode === 'existing')
        : activeTab === 'layout'
            ? (currentLayout.isValidating || currentLayout.isValidated || currentLayout.mode === 'existing' || (!currentLayout.data?.ingredient_list_id && !currentLayout.data?.ingredient_list))
            : (currentOrderList.isValidating || currentOrderList.isValidated || currentOrderList.mode === 'existing');

    // Pagination Logic Handlers
    const isPrevDisabled = activeTab === 'configuration' ? (configurations.length <= 1 || configIndex === 0)
        : activeTab === 'layout' ? (layouts.length <= 1 || layoutIndex === 0)
            : (orderLists.length <= 1 || orderListIndex === 0);

    const isNextDisabled = activeTab === 'configuration' ? (configurations.length <= 1 || configIndex === configurations.length - 1)
        : activeTab === 'layout' ? (layouts.length <= 1 || layoutIndex === layouts.length - 1)
            : (orderLists.length <= 1 || orderListIndex === orderLists.length - 1);

    const handlePrev = () => {
        if (activeTab === 'configuration') setConfigIndex(i => i - 1);
        else if (activeTab === 'layout') setLayoutIndex(i => i - 1);
        else setOrderListIndex(i => i - 1);
    };

    const handleNext = () => {
        if (activeTab === 'configuration') setConfigIndex(i => i + 1);
        else if (activeTab === 'layout') setLayoutIndex(i => i + 1);
        else setOrderListIndex(i => i + 1);
    };

    const currentCountDisplay = activeTab === 'configuration' ? `${configIndex + 1} / ${configurations.length}`
        : activeTab === 'layout' ? `${layoutIndex + 1} / ${layouts.length}`
            : `${orderListIndex + 1} / ${orderLists.length}`;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col max-h-[95vh] h-225">

                <div
                    className="px-6 border-b border-gray-200 flex justify-between items-center shrink-0 bg-white rounded-t-lg h-16">
                    <div className="w-1/3 flex items-center gap-4">
                        <h2 className="text-xl font-bold text-gray-900 shrink-0">Create Batch Fast</h2>
                        <input
                            type="text"
                            placeholder="Batch Name..."
                            value={batchName}
                            onChange={(e) => setBatchName(e.target.value)}
                            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 w-full max-w-40 shadow-sm"
                        />
                    </div>

                    <div className="flex space-x-6 h-full w-1/3 justify-center">
                        {[
                            {id: 'configuration', label: 'Configuration'},
                            {id: 'layout', label: 'Layout'},
                            {id: 'order_list', label: 'Order List'}
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as 'configuration' | 'layout' | 'order_list')}
                                className={`relative h-full px-2 text-sm font-medium transition-colors ${
                                    activeTab === tab.id ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                                }`}
                            >
                                {tab.label}
                                {activeTab === tab.id && (
                                    <span
                                        className="absolute bottom-0 left-0 w-full h-0.5 bg-gray-900 rounded-t-md"></span>
                                )}
                            </button>
                        ))}
                    </div>

                    <div className="w-1/3 flex justify-end items-center gap-3">
                        <div className="flex items-center space-x-2 border-r border-gray-300 pr-3">
                            <button
                                type="button"
                                onClick={handleAddEntity}
                                className="px-3 py-1.5 bg-black text-white text-sm font-medium rounded-md hover:bg-gray-800 shadow-sm transition-colors"
                                title={`Add ${entityLabel}`}
                            >
                                Add {entityLabel}
                            </button>

                            <button
                                type="submit"
                                form={formId}
                                disabled={currentMode === 'empty' || isValidateDisabled}
                                className="p-1.5 rounded-md transition-colors shadow-sm bg-black text-white hover:bg-gray-800 disabled:bg-gray-200 disabled:text-gray-400"
                                title={`Validate ${entityLabel}`}
                            >
                                {isCurrentValidated ? <CheckIcon className="w-5 h-5"/> :
                                    <CheckBadgeIcon className="w-5 h-5"/>}
                            </button>

                            <button
                                type="button"
                                onClick={handleRemoveOrResetCurrentEntity}
                                disabled={currentMode === 'empty'}
                                className="p-1.5 rounded-md transition-colors shadow-sm bg-white border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed"
                                title={`Discard/Remove ${entityLabel}`}
                            >
                                <TrashIcon className="w-5 h-5"/>
                            </button>
                        </div>

                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                title="Close">
                            <XMarkIcon className="w-6 h-6"/>
                        </button>
                    </div>
                </div>

                {batchError && (
                    <div
                        className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md shrink-0 flex items-center gap-2">
                        <ExclamationTriangleIcon className='w-5 h-5'/>
                        <div>{batchError}</div>
                    </div>
                )}

                {submitWarning && (
                    <div
                        className="mx-6 mt-4 p-3 bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-md shrink-0 flex justify-between items-center gap-2">
                        <div className='flex items-center gap-2'>
                            <ExclamationTriangleIcon className='w-5 h-5'/>
                            <div>{submitWarning}</div>
                        </div>
                        <button onClick={() => setSubmitWarning(null)}>
                            <XMarkIcon className='w-5 h-5'/>
                        </button>
                    </div>
                )}

                <div className="flex-1 min-h-0 bg-gray-50 relative flex flex-col">
                    <div className={activeTab === 'configuration' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentConfigurationTab ref={configTabRef} state={currentConfig}
                                                    setState={handleConfigChange}/>
                    </div>
                    <div className={activeTab === 'layout' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentLayoutTab ref={layoutTabRef} state={currentLayout} setState={handleLayoutChange}/>
                    </div>
                    <div className={activeTab === 'order_list' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentOrderListTab ref={orderListTabRef} state={currentOrderList}
                                                setState={handleOrderListChange}/>
                    </div>
                </div>

                <div
                    className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-between items-center shrink-0">
                    <div className="flex items-center space-x-2 w-1/3">
                        {activeTab === 'order_list' && currentOrderList.mode !== 'empty' && (
                            <button type="button" onClick={() => orderListTabRef.current?.triggerFileUpload()}
                                    className="p-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors shadow-sm"
                                    title="Load from File">
                                <ArrowUpTrayIcon className="w-5 h-5"/>
                            </button>
                        )}
                    </div>

                    <div className="flex items-center space-x-4 w-1/3 justify-center">
                        <button
                            onClick={handlePrev}
                            disabled={isPrevDisabled}
                            className="p-1.5 text-gray-500 hover:text-black hover:bg-gray-100 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                        >
                            <ChevronLeftIcon className="w-5 h-5"/>
                        </button>
                        <span className="text-sm font-medium text-gray-700 select-none capitalize">
                            {activeTab.replace('_', ' ')} {currentCountDisplay}
                        </span>
                        <button
                            onClick={handleNext}
                            disabled={isNextDisabled}
                            className="p-1.5 text-gray-500 hover:text-black hover:bg-gray-100 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                        >
                            <ChevronRightIcon className="w-5 h-5"/>
                        </button>
                    </div>

                    <div className="flex items-center space-x-4 w-1/3 justify-end">
                        <button type="button" onClick={handleDiscardEntireMatrix}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                            Discard
                        </button>
                        <button onClick={handleCreateBatchSoftMatrix}
                                disabled={isGlobalSubmitting || createMatrixMutation.isPending}
                                className="px-5 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center transition-colors shadow-sm">
                            {isGlobalSubmitting || createMatrixMutation.isPending ? 'Processing...' : 'Create Batch'}
                        </button>
                    </div>
                </div>

            </div>

            {confirmModalData && (
                <div
                    className="absolute inset-0 bg-black/30 backdrop-blur-[1px] z-60 flex items-center justify-center p-4">
                    <div
                        className="bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-sm flex flex-col animate-in fade-in zoom-in duration-200">
                        <div
                            className="px-4 py-3 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t-lg">
                            <h3 className="font-bold text-gray-900">Confirm Batch Creation</h3>
                            <button onClick={() => setConfirmModalData(null)}
                                    className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-200 transition-colors">
                                <XMarkIcon className="w-5 h-5"/>
                            </button>
                        </div>

                        <div className="p-6 flex flex-col gap-4 text-gray-800 bg-white">
                            {confirmModalData.warnings && (
                                <div
                                    className='p-3 bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-md flex flex-col gap-1'>
                                    <div className='font-semibold flex items-center gap-1.5'>
                                        <ExclamationTriangleIcon className='w-5 h-5'/>
                                        <div>Warnings ({confirmModalData.warnings.length})
                                        </div>
                                    </div>
                                    <div className='text-xs text-yellow-700 mt-1 max-h-20 overflow-y-auto pr-1'>
                                        {confirmModalData.warnings.join(' | ')}
                                    </div>
                                    <div className='text-xs mt-1 text-yellow-600 italic'>Batch creation allowed. The
                                        invalid combinations will be skipped.
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-between items-end border-b border-gray-100 pb-3">
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs uppercase tracking-wider font-semibold text-gray-500">To Create:</span>
                                    <span className="font-bold text-2xl text-black">{confirmModalData.amount}</span>
                                </div>
                                <div className="flex flex-col gap-1 text-right">
                                    <span
                                        className="text-xs uppercase tracking-wider font-semibold text-gray-500">Skipped:</span>
                                    <span className={`font-medium text-2xl text-black'`}>
                                        {confirmModalData.skipped}
                                    </span>
                                </div>
                            </div>

                            <div className="flex flex-col gap-1">
                                <span className="text-xs uppercase tracking-wider font-semibold text-gray-500">Estimated Duration:</span>
                                <span
                                    className="font-medium text-gray-800">{formatDuration(confirmModalData.duration)}</span>
                            </div>
                        </div>

                        <div className="px-5 py-4 border-t border-gray-200 flex justify-end bg-gray-50 rounded-b-lg">
                            <button
                                onClick={handleFinalConfirmMatrix}
                                disabled={isGlobalSubmitting}
                                className="px-6 py-2 text-sm font-medium text-white bg-black rounded-md hover:bg-gray-800 shadow-sm transition-colors disabled:opacity-50"
                            >
                                Confirm Creation
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}