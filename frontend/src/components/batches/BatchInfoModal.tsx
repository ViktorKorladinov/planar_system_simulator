import {useRef, useState} from 'react';
import {keepPreviousData, useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {deleteExperiment, getExperiments} from '../../api/experiments';
import {useAutoPageSize} from '../../hooks/useAutoPageSize';
import {
    formatBatchSize,
    formatDate,
    formatExperimentStatus,
    formatLayoutType,
    formatName,
    formatSolverType,
    formatWarmup
} from '../../utils/formatters';
import type {SortDirection, ToastMessage} from '../../types/common';
import type {ExperimentSortField} from '../../types/experiments';

// Shared UI Components
import SearchBar from '../common/SearchBar';
import FilterSelector, {type FilterCategory} from '../common/FilterSelector';
import DataTable from '../common/DataTable';
import SortableHeader from '../common/SortableHeader';
import Pagination from '../common/Pagination';
import ActionButtons from '../common/ActionButtons';
import ToastNotification from '../common/ToastNotification';

// Nested Modals
import ExperimentInfoModal from '../experiments/ExperimentInfoModal';
import ExperimentUpdateModal from '../experiments/ExperimentUpdateModal';
import {XMarkIcon} from '@heroicons/react/24/outline';

interface Props {
    batchId: number | null;
    onClose: () => void;
}

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

export default function BatchInfoModal({batchId, onClose}: Props) {
    const queryClient = useQueryClient();

    // Auto Sizing Refs
    const measureRef = useRef<HTMLDivElement>(null);
    const tableContainerRef = useRef<HTMLDivElement>(null);
    const {pageSize} = useAutoPageSize(measureRef, 61, 50, 40);

    // Filters and Pagination
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<ExperimentSortField>('created_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    // Notifications & Nested Modals
    const [toasts, setToasts] = useState<ToastMessage[]>([]);
    const [infoExpId, setInfoExpId] = useState<number | null>(null);
    const [updateExperiment, setUpdateExperiment] = useState<{ id: number, name: string } | null>(null);

    const {data, isLoading, isPlaceholderData} = useQuery({
        queryKey: ['experiments', {
            batchId,
            page,
            pageSize,
            sortBy,
            sortDir,
            appliedSearch,
            solvers: selectedFilters.solver,
            statuses: selectedFilters.experiment_status,
            layoutTypes: selectedFilters.layout_type
        }],
        queryFn: () => getExperiments(
            page, pageSize, sortBy, sortDir, appliedSearch,
            selectedFilters.experiment_status || [], selectedFilters.layout_type || [], selectedFilters.solver || [],
            batchId || undefined
        ),
        placeholderData: keepPreviousData,
        enabled: !!batchId,
    });

    const experiments = data?.experiments || [];
    const totalPages = data?.total || 1;
    const isLastExperimentInBatch = data?.experiments?.length === 1 && totalPages === 1;

    // Helpers
    const showToast = (message: string, type: 'success' | 'error', actionId?: number) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts(prev => [...prev, {id, message, type, actionId}]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
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

    // Mutations
    const deleteMutation = useMutation({
        mutationFn: ({id}: { id: number, name: string, isLast: boolean }) => deleteExperiment(id),
        onSuccess: async (_data, variables) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['batches']}),
                queryClient.invalidateQueries({queryKey: ['experiments']})
            ]);

            if (variables.isLast) {
                onClose();
            } else {
                showToast(`${variables.name} deleted successfully!`, "success");
            }
        },
        onError: (_data, variables) => showToast(`Failed to delete ${variables.name}.`, "error")
    });

    if (!batchId) return null;

    return (
        <>
            <div className="fixed inset-0 z-40 flex items-center justify-center p-6 bg-black/40 backdrop-blur-[1px]"
                 onClick={onClose}>

                <div
                    className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none items-center">
                    {toasts.map(toast => (
                        <ToastNotification
                            key={toast.id}
                            message={toast.message}
                            type={toast.type}
                        />
                    ))}
                </div>

                <div
                    className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-[95vw] flex flex-col max-h-[90vh] h-[90vh]"
                    onClick={e => e.stopPropagation()}>

                    <div
                        className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0 bg-white rounded-t-lg">
                        <div className="flex-1 min-w-0 flex items-center text-xl font-bold text-gray-900 gap-2">
                            <span className="shrink-0">Batch Details</span>
                            {data?.experiments[0].batch_name && (
                                <>
                                    <span className="shrink-0">-</span>
                                    <span className="truncate" title={data.experiments[0].batch_name}>
                            {data.experiments[0].batch_name}
                        </span>
                                </>
                            )}
                        </div>
                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-100 transition-colors shrink-0">
                            <XMarkIcon className="w-6 h-6"/>
                        </button>
                    </div>

                    <div className="p-4 border-b border-gray-200 shrink-0 flex items-center space-x-2 bg-gray-50/50">
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
                            onChange={(filters) => {
                                setSelectedFilters(filters);
                                setPage(1);
                            }}
                        />
                        {isPlaceholderData &&
                            <span className="text-sm text-gray-500 animate-pulse ml-4">Updating...</span>}
                    </div>

                    <div ref={measureRef} className="flex-1 min-h-0 p-4 bg-gray-50/50 flex flex-col relative">
                        <DataTable
                            containerRef={tableContainerRef}
                            headers={
                                <>
                                    <SortableHeader label="Name" field="name" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Status" field="status" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
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
                                    <SortableHeader label="Configuration Name" field="configuration_name"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Layout Name" field="layout_name" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Order List Name" field="order_list_name"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Tile Amount" field="tile_amount" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Interface Amount" field="interface_amount"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Dispenser Amount" field="dispenser_amount"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Batch Size" field="batch_size" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Warmup" field="warmup" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Interface Time" field="interface_time" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Dispensing Time" field="dispensing_time"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
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
                                    <td colSpan={23} className="text-center py-10 text-gray-500">Loading
                                        experiments...
                                    </td>
                                </tr>
                            ) : experiments.length === 0 ? (
                                <tr>
                                    <td colSpan={23} className="text-center py-10 text-gray-500">No experiments found.
                                    </td>
                                </tr>
                            ) : (
                                experiments.map((experiment) => (
                                    <tr key={experiment.id}
                                        className={`group hover:bg-gray-50 transition-opacity ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <ActionButtons
                                                onInfo={() => setInfoExpId(experiment.id!)}
                                                onEdit={() => setUpdateExperiment({
                                                    id: experiment.id!,
                                                    name: experiment.name || ''
                                                })}
                                                onDelete={() => {
                                                    const configName = experiment.name || 'Unnamed Experiment';
                                                    const msg = isLastExperimentInBatch
                                                        ? `Are you sure you want to delete ${configName}?\n\nWARNING: This is the last experiment in the batch. Deleting it will permanently delete the entire batch.`
                                                        : `Are you sure you want to delete ${configName}?`;

                                                    if (window.confirm(msg)) {
                                                        deleteMutation.mutate({
                                                            id: experiment.id!,
                                                            name: configName,
                                                            isLast: isLastExperimentInBatch
                                                        });
                                                    }
                                                }}
                                                deleteDisabled={deleteMutation.isPending}
                                            />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatName(experiment.name)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatExperimentStatus(experiment.status)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatSolverType(experiment.solver_type)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatLayoutType(experiment.layout_type)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.mover_amount}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.order_amount}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{experiment.time_limit}</td>
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
                    </div>

                    <div
                        className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex items-center justify-between shrink-0">
                        <div className="flex-1">
                            <Pagination
                                page={page}
                                totalPages={totalPages}
                                onPageChange={setPage}
                                isDisabled={isLoading || isPlaceholderData}
                            />
                        </div>
                    </div>
                </div>
            </div>

            <ExperimentInfoModal
                experimentId={infoExpId}
                onClose={() => setInfoExpId(null)}
            />

            {updateExperiment && (
                <ExperimentUpdateModal
                    config={updateExperiment}
                    onClose={() => setUpdateExperiment(null)}
                    onSuccess={(msg, id) => showToast(msg, "success", id)}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}
        </>
    );
}