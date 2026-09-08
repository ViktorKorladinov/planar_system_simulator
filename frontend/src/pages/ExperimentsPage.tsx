import FilterSelector, {type FilterCategory} from "../components/common/FilterSelector";
import {keepPreviousData, useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {useSearchParams} from "react-router-dom";
import {useRef, useState} from "react";
import type {SortDirection, ToastMessage} from "../types/common";
import {useAutoPageSize} from "../hooks/useAutoPageSize";
import ToastNotification from "../components/common/ToastNotification";
import SearchBar from "../components/common/SearchBar";
import DataTable from "../components/common/DataTable";
import SortableHeader from "../components/common/SortableHeader";
import ActionButtons from "../components/common/ActionButtons";
import {
    formatBatchSize,
    formatDate,
    formatExperimentStatus,
    formatLayoutType,
    formatName,
    formatSolverType,
    formatWarmup
} from "../utils/formatters";
import Pagination from "../components/common/Pagination";
import type {ExperimentSingleGetResponseDTO, ExperimentSortField} from "../types/experiments";
import {deleteExperiment, getExperiments} from "../api/experiments";
import ExperimentCreateModal from "../components/experiments/ExperimentCreateModal";
import ExperimentInfoModal from "../components/experiments/ExperimentInfoModal";
import ExperimentUpdateModal from "../components/experiments/ExperimentUpdateModal";

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'experiment_status',
        label: 'Status',
        options: [
            {label: 'Queued', value: 'queued'},
            {label: 'Running', value: 'running'},
            {label: 'Finished', value: 'finished'},
            {label: 'Failed', value: 'failed'}
        ]
    },
    {
        id: 'solver',
        label: 'Solver',
        options: [
            {label: 'Hexaly Medicine', value: 'hexaly'},
            {label: 'Cplex Medicine', value: 'cplex_medicine'},
            {label: 'Cplex Perfumes', value: 'cplex_perfumes'}
        ]
    },
    {
        id: 'layout_type',
        label: 'Layout',
        options: [
            {label: 'Line', value: 'line'},
            {label: 'Double Line', value: 'double_line'},
            {label: 'Square', value: 'square'},
            {label: 'Ring', value: 'ring'},
            {label: 'Custom', value: 'custom'}
        ]
    }
];

export default function ExperimentsPage() {
    const queryClient = useQueryClient();
    const [searchParams, setSearchParams] = useSearchParams();

    // Generic State
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<ExperimentSortField>('created_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    // Modal State
    const isCreateModalOpen = searchParams.get('create') === 'true';
    const [infoId, setInfoId] = useState<number | null>(null);
    const [updateExperiment, setUpdateExperiment] = useState<{ id: number, name: string } | null>(null);
    const [copyExperimentData, setCopyExperimentData] = useState<ExperimentSingleGetResponseDTO | null>(null);

    // Hook for Table Sizing
    const tableContainerRef = useRef<HTMLDivElement>(null);
    const {pageSize} = useAutoPageSize(tableContainerRef);

    // Filter Initialization
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    // Query Data
    const {data, isLoading, isError, isPlaceholderData} = useQuery({
        queryKey: ['experiments', {
            page, pageSize, sortBy, sortDir, appliedSearch, solvers: selectedFilters.solver,
            statuses: selectedFilters.experiment_status, layoutTypes: selectedFilters.layout_type
        }],
        queryFn: () => getExperiments(page, pageSize, sortBy, sortDir, appliedSearch,
            selectedFilters.experiment_status || [], selectedFilters.layout_type || [], selectedFilters.solver || []),
        placeholderData: keepPreviousData,
    });

    const experiments = data?.experiments || [];
    const totalPages = data?.total || 1;

    // Helpers
    const showToast = (message: string, type: 'success' | 'error', actionId?: number) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts(prev => [...prev, {id, message, type, actionId}]);
        setTimeout(() => {
            setToasts(prev => prev.filter(toast => toast.id !== id));
        }, 6000);
    };

    const handleSort = (field: string) => {
        const typedField = field as ExperimentSortField;
        if (sortBy === typedField) {
            setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(typedField);
            setSortDir('asc');
        }
        setPage(1);
    };

    const handleFilterChange = (newFilters: Record<string, string[]>) => {
        setSelectedFilters(newFilters);
        setPage(1);
    };

    // Mutations
    const deleteMutation = useMutation({
        mutationFn: ({id}: { id: number, name: string }) => deleteExperiment(id),
        onSuccess: async (_data, variables) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['batches']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']})
            ]);
            showToast(`${variables.name} deleted successfully!`, "success");
        },
        onError: (_data, variables) => showToast(`Failed to delete ${variables.name}.`, "error")
    });

    return (
        <div className="flex-1 flex flex-col min-h-0 p-6 max-w-[100vw] relative">

            {/* Overlay UI */}
            <div
                className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none items-center">
                {toasts.map(toast => (
                    <ToastNotification
                        key={toast.id}
                        message={toast.message}
                        type={toast.type}
                        actionText={toast.actionId ? "View Details" : undefined}
                        onActionClick={toast.actionId ? () => {
                            setInfoId(toast.actionId!);
                            setToasts(prev => prev.filter(t => t.id !== toast.id));
                        } : undefined}
                    />
                ))}
            </div>

            <ExperimentCreateModal
                isOpen={isCreateModalOpen}
                initialData={copyExperimentData}
                onClose={() => {
                    setCopyExperimentData(null);
                    searchParams.delete('create');
                    setSearchParams(searchParams);
                }}
                onSuccessSubmit={(name, id) => showToast(`${name} created successfully!`, "success", id)}
            />

            <ExperimentInfoModal
                experimentId={infoId}
                onClose={() => setInfoId(null)}
                onCopyCreate={(fullData) => {
                    setCopyExperimentData(fullData);
                    setInfoId(null);
                    searchParams.set('create', 'true');
                    setSearchParams(searchParams);
                }}
            />

            {updateExperiment && (
                <ExperimentUpdateModal
                    config={updateExperiment}
                    onClose={() => setUpdateExperiment(null)}
                    onSuccess={(msg, id) => showToast(msg, "success", id)}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <h1 className="text-3xl font-bold text-gray-900">Experiments</h1>
                {isPlaceholderData && <span className="text-sm text-gray-500 animate-pulse">Updating...</span>}
            </div>

            {/* Toolbar */}
            <div className="flex items-center space-x-2 mb-4 shrink-0">
                <SearchBar
                    value={searchInput}
                    onChange={setSearchInput}
                    onSearch={() => {
                        setAppliedSearch(searchInput);
                        setPage(1);
                    }}
                />

                <FilterSelector
                    categories={FILTER_CATEGORIES}
                    selectedValues={selectedFilters}
                    onChange={handleFilterChange}
                />
            </div>

            {isError && (
                <div className="text-red-500 mb-4 p-4 bg-red-50 rounded-md border border-red-200">
                    Failed to load experiments. Please make sure the backend is running.
                </div>
            )}

            <DataTable
                containerRef={tableContainerRef}
                headers={
                    <>
                        <SortableHeader label="Name" field="name" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Status" field="status" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Solver Type" field="solver_type" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Layout Type" field="layout_type" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Mover Amount" field="mover_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Order Amount" field="order_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Time Limit (s)" field="time_limit" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Batch Name" field="batch_name" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Configuration Name" field="configuration_name" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Layout Name" field="layout_name" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Order List Name" field="order_list_name" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Tile Amount" field="tile_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Interface Amount" field="interface_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Dispenser Amount" field="dispenser_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Batch Size" field="batch_size" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Warmup" field="warmup" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Interface Time" field="interface_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Dispensing TIme" field="dispensing_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Process Amount" field="process_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Created At" field="created_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Updated At" field="updated_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Started At" field="started_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Finished At" field="finished_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                    </>
                }
            >
                {isLoading ? (
                    <tr>
                        <td colSpan={24} className="text-center py-10 text-gray-500">Loading Experiments...</td>
                    </tr>
                ) : experiments.length === 0 ? (
                    <tr>
                        <td colSpan={24} className="text-center py-10 text-gray-500">No experiments found.</td>
                    </tr>
                ) : (
                    experiments.map((experiment) => (
                        <tr key={experiment.id}
                            className={`hover:bg-gray-50 transition-opacity ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                                <ActionButtons
                                    onInfo={() => setInfoId(experiment.id!)}
                                    onEdit={() => setUpdateExperiment({
                                        id: experiment.id!,
                                        name: experiment.name || ''
                                    })}
                                    onDelete={() => {
                                        const configName = experiment.name || 'Unnamed Experiment';
                                        if (window.confirm(`Are you sure you want to delete ${configName}?`)) {
                                            deleteMutation.mutate({id: experiment.id!, name: configName});
                                        }
                                    }}
                                    deleteDisabled={deleteMutation.isPending}
                                />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(experiment.name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatExperimentStatus(experiment.status)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatSolverType(experiment.solver_type)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatLayoutType(experiment.layout_type)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.mover_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.order_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.time_limit}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatName(experiment.batch_name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatName(experiment.configuration_name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatName(experiment.layout_name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatName(experiment.order_list_name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.tile_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.interface_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.dispenser_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatBatchSize(experiment.batch_size)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatWarmup(experiment.warmup)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.interface_time}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.dispensing_time}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.process_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(experiment.created_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(experiment.updated_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(experiment.started_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(experiment.finished_at)}</td>
                        </tr>
                    ))
                )}
            </DataTable>

            <Pagination
                page={page}
                totalPages={totalPages}
                onPageChange={setPage}
                isDisabled={isPlaceholderData}
            />
        </div>
    );
}