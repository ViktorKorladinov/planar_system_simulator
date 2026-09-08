import {useRef, useState} from 'react';
import {keepPreviousData, useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useSearchParams} from 'react-router-dom';
import {deleteConfiguration, getConfigurations} from '../api/configurations';
import type {ConfigurationSingleGetResponseDTO, ConfigurationSortField} from '../types/configurations';
import type {SortDirection, ToastMessage} from '../types/common';
import {useAutoPageSize} from '../hooks/useAutoPageSize';
import {
    formatBatchSize,
    formatCapperTime,
    formatDate,
    formatDispenseRate,
    formatMixerFinalTime,
    formatMixerPrimaryTime,
    formatMoverSpeed,
    formatName,
    formatSolverType,
    formatViscosityExponent,
    formatWarmup
} from '../utils/formatters';
import ToastNotification from '../components/common/ToastNotification';
import SearchBar from '../components/common/SearchBar';
import FilterSelector, {type FilterCategory} from '../components/common/FilterSelector.tsx';
import DataTable from '../components/common/DataTable';
import SortableHeader from '../components/common/SortableHeader';
import ActionButtons from '../components/common/ActionButtons';
import Pagination from '../components/common/Pagination';
import ConfigurationCreateModal from '../components/configurations/ConfigurationCreateModal.tsx';
import ConfigurationInfoModal from '../components/configurations/ConfigurationInfoModal';
import ConfigurationUpdateModal from '../components/configurations/ConfigurationUpdateModal';

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'solver',
        label: 'Solver',
        options: [
            {label: 'Hexaly Medicine', value: 'hexaly'},
            {label: 'Cplex Medicine', value: 'cplex_medicine'},
            {label: 'Cplex Perfumes', value: 'cplex_perfumes'}
        ]
    }];

export default function ConfigurationsPage() {
    const queryClient = useQueryClient();
    const [searchParams, setSearchParams] = useSearchParams();

    // Generic State
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<ConfigurationSortField>('created_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    // Modal State
    const isCreateModalOpen = searchParams.get('create') === 'true';
    const [infoId, setInfoId] = useState<number | null>(null);
    const [updateConfig, setUpdateConfig] = useState<{ id: number, name: string } | null>(null);
    const [copyData, setCopyData] = useState<ConfigurationSingleGetResponseDTO | null>(null);

    // Hook for Table Sizing
    const tableContainerRef = useRef<HTMLDivElement>(null);
    const {pageSize} = useAutoPageSize(tableContainerRef);

    // Filter Initialization
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    // Query Data
    const {data, isLoading, isError, isPlaceholderData} = useQuery({
        queryKey: ['configurations', {page, pageSize, sortBy, sortDir, appliedSearch, solvers: selectedFilters.solver}],
        queryFn: () => getConfigurations(page, pageSize, sortBy, sortDir, appliedSearch, selectedFilters.solver || []),
        placeholderData: keepPreviousData,
    });

    const configurations = data?.configurations || [];
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
        const typedField = field as ConfigurationSortField;
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

    const openCreateModal = () => {
        searchParams.set('create', 'true');
        setSearchParams(searchParams);
    };

    const closeCreateModal = () => {
        searchParams.delete('create');
        setSearchParams(searchParams);
        setCopyData(null);
    };

    // Mutations
    const deleteMutation = useMutation({
        mutationFn: ({id}: { id: number, name: string }) => deleteConfiguration(id),
        onSuccess: async (_data, variables) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['configurations']}),
                queryClient.invalidateQueries({queryKey: ['configuration']}),
                queryClient.invalidateQueries({queryKey: ['configurations_select']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']}),
                queryClient.invalidateQueries({queryKey: ['batches']})
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

            <ConfigurationCreateModal
                isOpen={isCreateModalOpen}
                initialData={copyData}
                onClose={closeCreateModal}
                onSuccessSubmit={(name, id) => showToast(`${name} created successfully!`, "success", id)}
            />

            <ConfigurationInfoModal
                configId={infoId}
                onClose={() => setInfoId(null)}
                onCopyCreate={(data) => {
                    setInfoId(null);
                    setCopyData(data);
                    openCreateModal();
                }}
            />

            {updateConfig && (
                <ConfigurationUpdateModal
                    config={updateConfig}
                    onClose={() => setUpdateConfig(null)}
                    onSuccess={(msg, id) => showToast(msg, "success", id)}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <h1 className="text-3xl font-bold text-gray-900">Configurations</h1>
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
                    Failed to load configurations. Please make sure the backend is running.
                </div>
            )}

            <DataTable
                containerRef={tableContainerRef}
                headers={
                    <>
                        <SortableHeader label="Name" field="name" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Solver" field="solver_type" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Movers" field="mover_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Time Limit (s)" field="time_limit" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Processes" field="process_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Interface Time" field="interface_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Dispensing Time" field="dispensing_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Batch Size" field="batch_size" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Warmup" field="warmup" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Dispense rate" field="dispense_rate" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Mover Speed" field="mover_speed" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Viscosity Exponent" field="viscosity_exponent" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Mixer Primary Time" field="mixer_primary_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Mixer Final Time" field="mixer_final_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Capper Time" field="capper_time" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Created At" field="created_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Updated At" field="updated_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                    </>
                }
            >
                {isLoading ? (
                    <tr>
                        <td colSpan={17} className="text-center py-10 text-gray-500">Loading configurations...</td>
                    </tr>
                ) : configurations.length === 0 ? (
                    <tr>
                        <td colSpan={17} className="text-center py-10 text-gray-500">No configurations found.</td>
                    </tr>
                ) : (
                    configurations.map((config) => (
                        <tr key={config.id}
                            className={`hover:bg-gray-50 transition-opacity ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                                <ActionButtons
                                    onInfo={() => setInfoId(config.id!)}
                                    onEdit={() => setUpdateConfig({id: config.id!, name: config.name || ''})}
                                    onDelete={() => {
                                        const configName = config.name || 'Unnamed Configuration';
                                        if (window.confirm(`Are you sure you want to delete ${configName}?`)) {
                                            deleteMutation.mutate({id: config.id!, name: configName});
                                        }
                                    }}
                                    deleteDisabled={deleteMutation.isPending}
                                />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(config.name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatSolverType(config.solver_type)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{config.mover_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{config.time_limit}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{config.process_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{config.interface_time}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{config.dispensing_time}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatBatchSize(config.batch_size)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatWarmup(config.warmup)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDispenseRate(config.dispense_rate)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatMoverSpeed(config.mover_speed)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatViscosityExponent(config.viscosity_exponent)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatMixerPrimaryTime(config.mixer_primary_time)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatMixerFinalTime(config.mixer_final_time)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCapperTime(config.capper_time)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(config.created_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(config.updated_at)}</td>
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