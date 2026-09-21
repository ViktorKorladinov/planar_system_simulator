import {type SyntheticEvent, useEffect, useRef, useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createExperiment} from '../../api/experiments';
import type {ExperimentSingleCreateRequestDTO, ExperimentSingleGetResponseDTO} from '../../types/experiments';
import type {ConfigurationSingleCreateRequestDTO} from '../../types/configurations';
import ExperimentConfigurationTab, {type ConfigTabRef} from './tabs/ExperimentConfigurationTab';
import type {LayoutSingleCreateRequestDTO} from "../../types/layouts";
import ExperimentLayoutTab, {type LayoutTabRef} from "./tabs/ExperimentLayoutTab";
import type {OrderListCreateRequestDTO} from "../../types/order_lists";
import ExperimentOrderListTab, {type OrderListTabRef} from './tabs/ExperimentOrderListTab';
import {checkSolverRateLimit, formatRemainingTime} from '../../utils/solverRateLimit';

interface Props {
    isOpen: boolean;
    initialData?: ExperimentSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

export type EntityState<T> = {
    mode: 'empty' | 'existing' | 'draft';
    id: number | null;
    data: T | null;
    isValidated: boolean;
    isValidating?: boolean;
};

export default function ExperimentCreateModal({isOpen, initialData, onClose, onSuccessSubmit}: Props) {
    const queryClient = useQueryClient();

    const [experimentName, setExperimentName] = useState('');
    const [activeTab, setActiveTab] = useState<'configuration' | 'layout' | 'order_list'>('configuration');
    const [globalError, setGlobalError] = useState<string | null>(null);
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

    const [configState, setConfigState] = useState<EntityState<ConfigurationSingleCreateRequestDTO>>({
        mode: 'empty',
        id: null,
        data: null,
        isValidated: false
    });
    const [layoutState, setLayoutState] = useState<EntityState<LayoutSingleCreateRequestDTO>>({
        mode: 'empty',
        id: null,
        data: null,
        isValidated: false
    });
    const [orderListState, setOrderListState] = useState<EntityState<OrderListCreateRequestDTO>>({
        mode: 'empty',
        id: null,
        data: null,
        isValidated: false
    });

    const configTabRef = useRef<ConfigTabRef>(null);
    const layoutTabRef = useRef<LayoutTabRef>(null);
    const orderListTabRef = useRef<OrderListTabRef>(null);

    const [lastCopiedId, setLastCopiedId] = useState<number | null>(null);

    // Initialization logic for Copy & Create
    if (initialData && initialData.id !== lastCopiedId) {
        setLastCopiedId(initialData.id);
        setExperimentName(initialData.name ? `${initialData.name} (Copy)` : 'Copy');
        setActiveTab('configuration');

        const extractId = (obj: unknown): number | null => {
            if (obj && typeof obj === 'object' && 'id' in obj) {
                return typeof (obj as { id: unknown }).id === 'number' ? (obj as { id: number }).id : null;
            }
            return null;
        };

        const configId = extractId(initialData.configuration) ?? (initialData as unknown as {
            configuration_id?: number
        }).configuration_id ?? null;
        const layoutId = extractId(initialData.layout) ?? (initialData as unknown as {
            layout_id?: number
        }).layout_id ?? null;
        const orderListId = extractId(initialData.order_list) ?? (initialData as unknown as {
            order_list_id?: number
        }).order_list_id ?? null;

        setConfigState({
            mode: configId ? 'existing' : 'draft',
            id: configId,
            data: initialData.configuration as unknown as ConfigurationSingleCreateRequestDTO,
            isValidated: true,
            isValidating: false
        });

        setLayoutState({
            mode: layoutId ? 'existing' : 'draft',
            id: layoutId,
            data: initialData.layout as unknown as LayoutSingleCreateRequestDTO,
            isValidated: true,
            isValidating: false
        });

        setOrderListState({
            mode: orderListId ? 'existing' : 'draft',
            id: orderListId,
            data: initialData.order_list as unknown as OrderListCreateRequestDTO,
            isValidated: true,
            isValidating: false
        });

        setGlobalError(null);
    }

    const mutation = useMutation({
        mutationFn: async (payload: ExperimentSingleCreateRequestDTO) => {
            setGlobalError(null);
            await createExperiment(payload, true);
            return await createExperiment(payload, false);
        },
        onSuccess: async (createdData) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['batches']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']})
            ]);
            onSuccessSubmit(createdData.name, createdData.id);
            handleFullDiscard();
            onClose();
        },
        onError: (errors: unknown) => {
            if (Array.isArray(errors)) setGlobalError(errors.join(' | '));
            else if (typeof errors === 'string') setGlobalError(errors);
            else setGlobalError("An unexpected error occurred while saving the experiment.");
        },
        onSettled: () => {
            setIsGlobalSubmitting(false);
        }
    });

    const handleFullDiscard = () => {
        setExperimentName('');
        setActiveTab('configuration');
        setConfigState({mode: 'empty', id: null, data: null, isValidated: false});
        setLayoutState({mode: 'empty', id: null, data: null, isValidated: false});
        setOrderListState({mode: 'empty', id: null, data: null, isValidated: false});
        setLastCopiedId(null);
        setGlobalError(null);
    };

    const handleDiscardEntireExperiment = () => {
        if (window.confirm("Are you sure you want to discard the entire experiment?")) {
            handleFullDiscard();
            onClose();
        }
    };

    const handleSubmit = async (e: SyntheticEvent) => {
        e.preventDefault();
        if (isGlobalSubmitting || mutation.isPending) return;

        const missing = [];
        if (configState.mode === 'empty') missing.push("Configuration");
        if (layoutState.mode === 'empty') missing.push("Layout");
        if (orderListState.mode === 'empty') missing.push("Order List");

        if (missing.length > 0) {
            setGlobalError(`Please provide the following before creating: ${missing.join(', ')}`);
            return;
        }

        if (!layoutState.data?.ingredient_list_id && !layoutState.data?.ingredient_list) {
            setGlobalError("Please choose ingredient list for layout before creating an experiment.");
            return;
        }

        setGlobalError(null);
        setIsGlobalSubmitting(true);

        let allValid = true;
        let finalConfig: ConfigurationSingleCreateRequestDTO | null = configState.data;
        let finalLayout: LayoutSingleCreateRequestDTO | null = layoutState.data;
        let finalOrderList: OrderListCreateRequestDTO | null = orderListState.data;

        if (configState.mode === 'draft' && !configState.isValidated) {
            const validatedConfig = await configTabRef.current?.validate();
            if (!validatedConfig) allValid = false;
            else finalConfig = validatedConfig;
        }

        if (layoutState.mode === 'draft' && !layoutState.isValidated) {
            const validatedLayout = await layoutTabRef.current?.validate();
            if (!validatedLayout) allValid = false;
            else finalLayout = validatedLayout;
        }

        if (orderListState.mode === 'draft' && !orderListState.isValidated) {
            const validatedOrderList = await orderListTabRef.current?.validate();
            if (!validatedOrderList) allValid = false;
            else finalOrderList = validatedOrderList;
        }

        if (!allValid) {
            setGlobalError("Validation failed. Please check the respective tabs for specific errors.");
            setIsGlobalSubmitting(false);
            return;
        }

        const payload: Partial<ExperimentSingleCreateRequestDTO> = {};
        const trimmedName = experimentName.trim();

        if (trimmedName.length > 0) {
            payload.name = trimmedName;
        }

        if (configState.mode === 'existing' && configState.id !== null) {
            payload.configuration_id = configState.id;
            payload.configuration = null as unknown as ConfigurationSingleCreateRequestDTO;
        } else {
            payload.configuration_id = null as unknown as number;
            payload.configuration = finalConfig!;
        }

        if (layoutState.mode === 'existing' && layoutState.id !== null) {
            payload.layout_id = layoutState.id;
            payload.layout = null as unknown as LayoutSingleCreateRequestDTO;
        } else {
            payload.layout_id = null as unknown as number;
            payload.layout = finalLayout!;
        }

        if (orderListState.mode === 'existing' && orderListState.id !== null) {
            payload.order_list_id = orderListState.id;
            payload.order_list = null as unknown as OrderListCreateRequestDTO;
        } else {
            payload.order_list_id = null as unknown as number;
            payload.order_list = finalOrderList!;
        }

        mutation.mutate(payload as ExperimentSingleCreateRequestDTO);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col max-h-[95vh] h-225">

                <div
                    className="px-6 border-b border-gray-200 flex justify-between items-center shrink-0 bg-white rounded-t-lg h-16">
                    <div className="w-1/3">
                        <h2 className="text-xl font-bold text-gray-900 shrink-0">Create Experiment</h2>
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

                    <div className="w-1/3 flex justify-end items-center gap-4">
                        <input
                            type="text"
                            placeholder="Experiment Name..."
                            value={experimentName}
                            onChange={(e) => setExperimentName(e.target.value)}
                            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 w-full max-w-50 shadow-sm"
                        />
                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                title="Close">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
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

                {globalError && (
                    <div
                        className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md shrink-0">
                        {globalError}
                    </div>
                )}

                <div className="flex-1 min-h-0 bg-gray-50 relative flex flex-col">
                    <div className={activeTab === 'configuration' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentConfigurationTab ref={configTabRef} state={configState} setState={setConfigState}/>
                    </div>
                    <div className={activeTab === 'layout' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentLayoutTab ref={layoutTabRef} state={layoutState} setState={setLayoutState}/>
                    </div>
                    <div className={activeTab === 'order_list' ? 'flex-1 min-h-0' : 'hidden'}>
                        <ExperimentOrderListTab ref={orderListTabRef} state={orderListState}
                                                setState={setOrderListState}/>
                    </div>
                </div>

                <div
                    className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-between items-center shrink-0">
                    <div className="flex items-center space-x-3">
                        {activeTab === 'configuration' && configState.mode !== 'empty' && (
                            <>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this configuration?")) configTabRef.current?.discard();
                                }}
                                        className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                                    Discard Configuration
                                </button>
                                <button type="submit" form="config-tab-form"
                                        disabled={configState.isValidating || configState.isValidated || configState.mode === 'existing'}
                                        className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm">
                                    {configState.isValidating ? 'Validating...' : configState.isValidated ? 'Validated ✓' : 'Validate Configuration'}
                                </button>
                            </>
                        )}
                        {activeTab === 'layout' && layoutState.mode !== 'empty' && (
                            <>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this layout?")) layoutTabRef.current?.discard();
                                }}
                                        className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                                    Discard Layout
                                </button>
                                <button type="submit" form="layout-tab-form"
                                        disabled={layoutState.isValidating || layoutState.isValidated || layoutState.mode === 'existing' || (!layoutState.data?.ingredient_list_id && !layoutState.data?.ingredient_list)}
                                        className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm">
                                    {layoutState.isValidating ? 'Validating...' : layoutState.isValidated ? 'Validated ✓' : 'Validate Layout'}
                                </button>
                            </>
                        )}
                        {activeTab === 'order_list' && orderListState.mode !== 'empty' && (
                            <>
                                <button type="button" onClick={() => orderListTabRef.current?.triggerFileUpload()}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors shadow-sm flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                                    </svg>
                                    Load from File
                                </button>
                                <button type="button" onClick={() => {
                                    if (window.confirm("Are you sure you want to discard this order list?")) orderListTabRef.current?.discard();
                                }}
                                        className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                                    Discard Order List
                                </button>
                                <button type="submit" form="order-list-tab-form"
                                        disabled={orderListState.isValidating || orderListState.isValidated || orderListState.mode === 'existing'}
                                        className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-black disabled:opacity-50 transition-colors shadow-sm">
                                    {orderListState.isValidating ? 'Validating...' : orderListState.isValidated ? 'Validated ✓' : 'Validate Order List'}
                                </button>
                            </>
                        )}
                    </div>

                    <div className="flex items-center space-x-4">
                        <button type="button" onClick={handleDiscardEntireExperiment}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors">
                            Discard Entire Experiment
                        </button>
                        <button onClick={handleSubmit} disabled={isGlobalSubmitting || mutation.isPending || !!rateLimitRemaining}
                                className="px-5 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center transition-colors shadow-sm">
                            {rateLimitRemaining ? `Available in ${rateLimitRemaining}` : isGlobalSubmitting || mutation.isPending ? 'Processing...' : 'Create Experiment'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}