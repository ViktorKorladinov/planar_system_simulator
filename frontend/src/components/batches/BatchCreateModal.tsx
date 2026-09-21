import {type SyntheticEvent, useEffect, useRef, useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createExperiment} from '../../api/experiments';
import {createBatch} from '../../api/batches';
import type {ExperimentSingleCreateRequestDTO} from '../../types/experiments';
import type {ExperimentBatchCreateRequestDTO} from '../../types/batches';
import type {ConfigurationSingleCreateRequestDTO} from '../../types/configurations';
import type {LayoutSingleCreateRequestDTO} from "../../types/layouts";
import type {OrderListCreateRequestDTO} from "../../types/order_lists";
import ExperimentConfigurationTab, {type ConfigTabRef} from '../experiments/tabs/ExperimentConfigurationTab';
import ExperimentLayoutTab, {type LayoutTabRef} from "../experiments/tabs/ExperimentLayoutTab";
import ExperimentOrderListTab, {type OrderListTabRef} from '../experiments/tabs/ExperimentOrderListTab';
import type {EntityState} from '../experiments/ExperimentCreateModal';
import {checkSolverRateLimit, formatRemainingTime} from '../../utils/solverRateLimit';
import {
    ArrowUpTrayIcon,
    CheckBadgeIcon,
    CheckIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    PlusIcon,
    TrashIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

type ExperimentUIState = {
    id: string;
    name: string;
    configState: EntityState<ConfigurationSingleCreateRequestDTO>;
    layoutState: EntityState<LayoutSingleCreateRequestDTO>;
    orderListState: EntityState<OrderListCreateRequestDTO>;
    error: string | null;
    isValidated: boolean;
};

const createDefaultExperimentState = (): ExperimentUIState => ({
    id: crypto.randomUUID(),
    name: '',
    configState: {
        mode: 'empty',
        id: null,
        data: null,
        isValidated: false
    } as EntityState<ConfigurationSingleCreateRequestDTO>,
    layoutState: {mode: 'empty', id: null, data: null, isValidated: false} as EntityState<LayoutSingleCreateRequestDTO>,
    orderListState: {mode: 'empty', id: null, data: null, isValidated: false} as EntityState<OrderListCreateRequestDTO>,
    error: null,
    isValidated: false,
});

function formatDuration(totalSeconds: number): string {
    const days = Math.floor(totalSeconds / (3600 * 24));
    const hours = Math.floor((totalSeconds % (3600 * 24)) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);

    const parts = [];
    if (days > 0) parts.push(`${days} days`);
    if (hours > 0) parts.push(`${hours} hours`);
    if (minutes > 0) parts.push(`${minutes} minutes`);
    if (seconds > 0 || parts.length === 0) parts.push(`${seconds} seconds`);

    return parts.join(', ');
}

export default function BatchCreateModal({isOpen, onClose, onSuccessSubmit}: Props) {
    const queryClient = useQueryClient();

    const [batchName, setBatchName] = useState('');
    const [experiments, setExperiments] = useState<ExperimentUIState[]>([createDefaultExperimentState()]);
    const [currentIndex, setCurrentIndex] = useState(0);

    const [activeTab, setActiveTab] = useState<'configuration' | 'layout' | 'order_list'>('configuration');
    const [batchError, setBatchError] = useState<string | null>(null);
    const [isGlobalSubmitting, setIsGlobalSubmitting] = useState(false);

    const [rateLimitRemaining, setRateLimitRemaining] = useState<string | null>(null);
    useEffect(() => {
        const tick = () => {
            const {allowed, remainingMs} = checkSolverRateLimit();
            setRateLimitRemaining(allowed ? null : formatRemainingTime(remainingMs));
        };
        tick();
        const interval = setInterval(tick, 1000);
        return () => clearInterval(interval);
    }, []);
    const [confirmModalData, setConfirmModalData] = useState<{
        amount: number,
        duration: number,
        payload: ExperimentBatchCreateRequestDTO
    } | null>(null);

    const configTabRef = useRef<ConfigTabRef>(null);
    const layoutTabRef = useRef<LayoutTabRef>(null);
    const orderListTabRef = useRef<OrderListTabRef>(null);

    const currentExp = experiments[currentIndex];

    const updateCurrentExp = (updater: (prev: ExperimentUIState) => ExperimentUIState) => {
        setExperiments(prev => prev.map((exp, i) => i === currentIndex ? updater(exp) : exp));
    };

    const handleConfigChange = (updater: (prev: EntityState<ConfigurationSingleCreateRequestDTO>) => EntityState<ConfigurationSingleCreateRequestDTO>) => {
        updateCurrentExp(prev => ({
            ...prev,
            isValidated: false,
            configState: updater(prev.configState)
        }));
    };

    const handleLayoutChange = (updater: (prev: EntityState<LayoutSingleCreateRequestDTO>) => EntityState<LayoutSingleCreateRequestDTO>) => {
        updateCurrentExp(prev => ({
            ...prev,
            isValidated: false,
            layoutState: updater(prev.layoutState)
        }));
    };

    const handleOrderListChange = (updater: (prev: EntityState<OrderListCreateRequestDTO>) => EntityState<OrderListCreateRequestDTO>) => {
        updateCurrentExp(prev => ({
            ...prev,
            isValidated: false,
            orderListState: updater(prev.orderListState)
        }));
    };

    const buildExperimentPayload = (exp: ExperimentUIState): ExperimentSingleCreateRequestDTO | null => {
        if (exp.configState.mode === 'empty' || exp.layoutState.mode === 'empty' || exp.orderListState.mode === 'empty') return null;
        if (!exp.layoutState.data?.ingredient_list_id && !exp.layoutState.data?.ingredient_list) return null;

        const payload: Partial<ExperimentSingleCreateRequestDTO> = {};
        const trimmedName = exp.name.trim();

        payload.name = trimmedName.length > 0 ? trimmedName : (null as unknown as string);

        if (exp.configState.mode === 'existing' && exp.configState.id !== null) {
            payload.configuration_id = exp.configState.id;
            payload.configuration = null as unknown as ConfigurationSingleCreateRequestDTO;
        } else {
            payload.configuration_id = null as unknown as number;
            payload.configuration = exp.configState.data!;
        }

        if (exp.layoutState.mode === 'existing' && exp.layoutState.id !== null) {
            payload.layout_id = exp.layoutState.id;
            payload.layout = null as unknown as LayoutSingleCreateRequestDTO;
        } else {
            const layoutData = exp.layoutState.data!;
            const isDraftIngList = layoutData.ingredient_list && !('id' in layoutData.ingredient_list);

            payload.layout_id = null as unknown as number;
            payload.layout = {
                ...layoutData,
                ingredient_list_id: isDraftIngList ? null : (layoutData.ingredient_list_id ?? (layoutData.ingredient_list as {
                    id?: number
                })?.id ?? null),
                ingredient_list: isDraftIngList ? layoutData.ingredient_list : null,
                tiles: layoutData.tiles.map(t => ({
                    x: t.x,
                    y: t.y,
                    type: t.type,
                    dispensed_types: t.type === 'dispenser' ? t.dispensed_types : (null as unknown as string[])
                }))
            };
        }

        if (exp.orderListState.mode === 'existing' && exp.orderListState.id !== null) {
            payload.order_list_id = exp.orderListState.id;
            payload.order_list = null as unknown as OrderListCreateRequestDTO;
        } else {
            const orderData = exp.orderListState.data!;
            payload.order_list_id = null as unknown as number;
            payload.order_list = {
                name: orderData.name?.trim() || (null as unknown as string),
                type: orderData.type,
                orders: orderData.orders.map(o => ({
                    items: o.items.map(i => {
                        const isSpecial = i.name.toLowerCase() === 'mixer' || i.name.toLowerCase() === 'capper';
                        return {
                            name: isSpecial ? i.name.trim().toLowerCase() : i.name.trim(),
                            quantity: isSpecial ? 0 : Number(i.quantity)
                        };
                    }),
                    t_max: orderData.type === 'perfume' ? (o.t_max !== null ? Number(o.t_max) : null) : null
                }))
            };
        }

        return payload as ExperimentSingleCreateRequestDTO;
    };

    const validateExperimentMutation = useMutation({
        mutationFn: async (payload: ExperimentSingleCreateRequestDTO) => {
            await createExperiment(payload, true);
        },
        onSuccess: () => {
            updateCurrentExp(prev => ({...prev, isValidated: true, error: null}));
        },
        onError: (errors: unknown) => {
            updateCurrentExp(prev => ({
                ...prev,
                isValidated: false,
                error: Array.isArray(errors) ? errors.join(' | ') : typeof errors === 'string' ? errors : "Validation failed."
            }));
        }
    });

    const handleValidateCurrent = async () => {
        updateCurrentExp(prev => ({...prev, error: null}));
        const payload = buildExperimentPayload(currentExp);

        if (!payload) {
            updateCurrentExp(prev => ({
                ...prev,
                error: "Please ensure Configuration, Layout, and Order List are completely provided and an Ingredient List is selected."
            }));
            return;
        }

        validateExperimentMutation.mutate(payload);
    };

    const handleAddExperiment = () => {
        setExperiments(prev => [...prev, createDefaultExperimentState()]);
        setCurrentIndex(experiments.length);
    };

    const handleRemoveCurrent = () => {
        if (window.confirm("Are you sure you want to remove this experiment from the batch?")) {
            setExperiments(prev => {
                const newExps = prev.filter((_, i) => i !== currentIndex);
                if (newExps.length === 0) return [createDefaultExperimentState()];
                return newExps;
            });
            setCurrentIndex(prev => Math.max(0, prev - 1));
        }
    };

    const handleDiscardBatch = () => {
        if (window.confirm("Are you sure you want to discard the entire batch?")) {
            setBatchName('');
            setExperiments([createDefaultExperimentState()]);
            setCurrentIndex(0);
            setActiveTab('configuration');
            setBatchError(null);
            onClose();
        }
    };

    const createBatchMutation = useMutation({
        mutationFn: async ({payload, isDryRun}: { payload: ExperimentBatchCreateRequestDTO, isDryRun: boolean }) => {
            return await createBatch(payload, isDryRun);
        },
        onSuccess: async (data, variables) => {
            if (variables.isDryRun) {
                if (data.errors && data.errors.length > 0) {
                    setBatchError(data.errors.join(' | '));
                } else if (data.created_amount === 0) {
                    setBatchError("Validation failed: No valid experiments could be created.");
                } else {
                    setBatchError(null);
                    setConfirmModalData({
                        amount: data.created_amount,
                        duration: data.estimated_time,
                        payload: variables.payload
                    });
                }
            } else {
                await Promise.all([
                    queryClient.invalidateQueries({queryKey: ['batches']}),
                    queryClient.invalidateQueries({queryKey: ['experiments']})
                ]);
                onSuccessSubmit(data.name, data.id);
                setBatchName('');
                setExperiments([createDefaultExperimentState()]);
                setCurrentIndex(0);
                setConfirmModalData(null);
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
                    setBatchError(
                        typeof apiError.detail === 'string'
                            ? apiError.detail
                            : JSON.stringify(apiError.detail)
                    );
                    return;
                }
            }

            if (Array.isArray(err)) setBatchError(err.join(' | '));
            else if (typeof err === 'string') setBatchError(err);
            else setBatchError("Validation failed. Please check your inputs.");
        },
        onSettled: () => {
            setIsGlobalSubmitting(false);
        }
    });

    const handleCreateBatchSoft = async (e: SyntheticEvent) => {
        e.preventDefault();
        if (isGlobalSubmitting || createBatchMutation.isPending) return;

        setBatchError(null);
        setIsGlobalSubmitting(true);

        const expPayloads: ExperimentSingleCreateRequestDTO[] = [];

        for (let i = 0; i < experiments.length; i++) {
            const payload = buildExperimentPayload(experiments[i]);
            if (!payload) {
                setBatchError(`Experiment ${i + 1} is missing a Configuration, Layout, Order List, or Ingredient List selection.`);
                setIsGlobalSubmitting(false);
                return;
            }
            expPayloads.push(payload);
        }

        const payload: ExperimentBatchCreateRequestDTO = {
            name: batchName.trim() ? batchName.trim() : (null as unknown as string),
            experiments: expPayloads
        };

        createBatchMutation.mutate({payload, isDryRun: true});
    };

    const handleFinalConfirm = () => {
        if (!confirmModalData) return;
        setIsGlobalSubmitting(true);
        createBatchMutation.mutate({payload: confirmModalData.payload, isDryRun: false});
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col max-h-[95vh] h-225">

                <div
                    className="px-6 border-b border-gray-200 flex justify-between items-center shrink-0 bg-white rounded-t-lg h-16">
                    <div className="w-1/3 flex items-center gap-4">
                        <h2 className="text-xl font-bold text-gray-900 shrink-0">Create Batch</h2>
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
                        <input
                            type="text"
                            placeholder="Experiment Name..."
                            value={currentExp.name}
                            onChange={(e) => updateCurrentExp(prev => ({
                                ...prev,
                                name: e.target.value,
                                isValidated: false
                            }))}
                            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 w-full max-w-40 shadow-sm"
                        />

                        <div className="flex items-center space-x-1 border-r border-gray-300 pr-3">
                            <button
                                onClick={handleAddExperiment}
                                className="p-1.5 bg-gray-900 text-white rounded-md hover:bg-black shadow-sm transition-colors"
                                title="Add Experiment"
                            >
                                <PlusIcon className="w-5 h-5"/>
                            </button>
                            <button
                                onClick={handleValidateCurrent}
                                disabled={currentExp.isValidated || validateExperimentMutation.isPending}
                                className={`p-1.5 rounded-md transition-colors ${currentExp.isValidated ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-gray-900 text-white hover:bg-black shadow-sm'}`}
                                title="Validate Current Experiment"
                            >
                                {currentExp.isValidated ? <CheckIcon className="w-5 h-5"/> :
                                    <CheckBadgeIcon className="w-5 h-5"/>}
                            </button>
                            <button
                                onClick={handleRemoveCurrent}
                                className="p-1.5 bg-white border border-red-500 text-red-500 rounded-md hover:bg-red-50 shadow-sm transition-colors"
                                title="Remove Experiment"
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

                {rateLimitRemaining && (
                    <div
                        className="mx-6 mt-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-md shrink-0 flex items-center gap-2">
                        <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span>
                            <strong>Solver rate limited</strong> — you can run the solver once per hour. Next run available in <strong>{rateLimitRemaining}</strong>.
                        </span>
                    </div>
                )}

                {(batchError || currentExp.error) && (
                    <div
                        className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md shrink-0 flex flex-col gap-1">
                        {batchError && <div><strong>Batch Error:</strong> {batchError}</div>}
                        {currentExp.error && <div><strong>Experiment Error:</strong> {currentExp.error}</div>}
                    </div>
                )}

                <div className="flex-1 min-h-0 bg-gray-50 relative flex flex-col">
                    <div className={activeTab === 'configuration' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentConfigurationTab ref={configTabRef} state={currentExp.configState}
                                                    setState={handleConfigChange}/>
                    </div>
                    <div className={activeTab === 'layout' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentLayoutTab ref={layoutTabRef} state={currentExp.layoutState}
                                             setState={handleLayoutChange}/>
                    </div>
                    <div className={activeTab === 'order_list' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentOrderListTab ref={orderListTabRef} state={currentExp.orderListState}
                                                setState={handleOrderListChange}/>
                    </div>
                </div>

                <div
                    className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-between items-center shrink-0">
                    <div className="flex items-center space-x-2 w-1/3">
                        {activeTab === 'configuration' && currentExp.configState.mode !== 'empty' && (
                            <>
                                <button type="submit" form="config-tab-form"
                                        disabled={currentExp.configState.isValidating || currentExp.configState.isValidated || currentExp.configState.mode === 'existing'}
                                        className="p-2 text-white bg-gray-900 rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm"
                                        title="Validate Configuration">
                                    {currentExp.configState.isValidated ? <CheckIcon className="w-5 h-5"/> :
                                        <CheckBadgeIcon className="w-5 h-5"/>}
                                </button>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this configuration?")) configTabRef.current?.discard();
                                }}
                                        className="p-2 text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors shadow-sm"
                                        title="Discard Configuration">
                                    <TrashIcon className="w-5 h-5"/>
                                </button>
                            </>
                        )}
                        {activeTab === 'layout' && currentExp.layoutState.mode !== 'empty' && (
                            <>
                                <button type="submit" form="layout-tab-form"
                                        disabled={currentExp.layoutState.isValidating || currentExp.layoutState.isValidated || currentExp.layoutState.mode === 'existing' || (!currentExp.layoutState.data?.ingredient_list_id && !currentExp.layoutState.data?.ingredient_list)}
                                        className="p-2 text-white bg-gray-900 rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm"
                                        title="Validate Layout">
                                    {currentExp.layoutState.isValidated ? <CheckIcon className="w-5 h-5"/> :
                                        <CheckBadgeIcon className="w-5 h-5"/>}
                                </button>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this layout?")) layoutTabRef.current?.discard();
                                }}
                                        className="p-2 text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors shadow-sm"
                                        title="Discard Layout">
                                    <TrashIcon className="w-5 h-5"/>
                                </button>
                            </>
                        )}
                        {activeTab === 'order_list' && currentExp.orderListState.mode !== 'empty' && (
                            <>
                                <button type="button" onClick={() => orderListTabRef.current?.triggerFileUpload()}
                                        className="p-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors shadow-sm"
                                        title="Load from File">
                                    <ArrowUpTrayIcon className="w-5 h-5"/>
                                </button>
                                <button type="submit" form="order-list-tab-form"
                                        disabled={currentExp.orderListState.isValidating || currentExp.orderListState.isValidated || currentExp.orderListState.mode === 'existing'}
                                        className="p-2 text-white bg-gray-900 rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm"
                                        title="Validate Order List">
                                    {currentExp.orderListState.isValidated ? <CheckIcon className="w-5 h-5"/> :
                                        <CheckBadgeIcon className="w-5 h-5"/>}
                                </button>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this order list?")) orderListTabRef.current?.discard();
                                }}
                                        className="p-2 text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors shadow-sm"
                                        title="Discard Order List">
                                    <TrashIcon className="w-5 h-5"/>
                                </button>
                            </>
                        )}
                    </div>

                    <div className="flex items-center space-x-4 w-1/3 justify-center">
                        <button
                            onClick={() => setCurrentIndex(i => i - 1)}
                            disabled={experiments.length <= 1 || currentIndex === 0}
                            className="p-1.5 text-gray-500 hover:text-black hover:bg-gray-100 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                        >
                            <ChevronLeftIcon className="w-5 h-5"/>
                        </button>
                        <span className="text-sm font-medium text-gray-700 select-none">
                            Experiment {currentIndex + 1} / {experiments.length}
                        </span>
                        <button
                            onClick={() => setCurrentIndex(i => i + 1)}
                            disabled={experiments.length <= 1 || currentIndex === experiments.length - 1}
                            className="p-1.5 text-gray-500 hover:text-black hover:bg-gray-100 rounded-md transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
                        >
                            <ChevronRightIcon className="w-5 h-5"/>
                        </button>
                    </div>

                    <div className="flex items-center space-x-4 w-1/3 justify-end">
                        <button type="button" onClick={handleDiscardBatch}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                            Discard Batch
                        </button>
                        <button onClick={handleCreateBatchSoft}
                                disabled={isGlobalSubmitting || createBatchMutation.isPending || !!rateLimitRemaining}
                                className="px-5 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center transition-colors shadow-sm">
                            {rateLimitRemaining ? `Available in ${rateLimitRemaining}` : isGlobalSubmitting || createBatchMutation.isPending ? 'Processing...' : 'Create Batch'}
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
                            <div className="flex flex-col gap-1 border-b border-gray-100 pb-3">
                                <span className="text-xs uppercase tracking-wider font-semibold text-gray-500">Amount of Experiments:</span>
                                <span className="font-bold text-xl text-gray-900">{confirmModalData.amount}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-xs uppercase tracking-wider font-semibold text-gray-500">Estimated Duration:</span>
                                <span
                                    className="font-medium text-gray-800">{formatDuration(confirmModalData.duration)}</span>
                            </div>
                        </div>

                        <div className="px-5 py-4 border-t border-gray-200 flex justify-end bg-gray-50 rounded-b-lg">
                            <button
                                onClick={handleFinalConfirm}
                                disabled={isGlobalSubmitting}
                                className="px-6 py-2 text-sm font-medium text-white bg-black rounded-md hover:bg-gray-800 shadow-sm transition-colors disabled:opacity-50"
                            >
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}