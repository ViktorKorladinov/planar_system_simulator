import {keepPreviousData, useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {useSearchParams} from "react-router-dom";
import {useRef, useState} from "react";
import type {SortDirection, ToastMessage} from "../types/common.ts";
import {useAutoPageSize} from "../hooks/useAutoPageSize.ts";
import ToastNotification from "../components/common/ToastNotification.tsx";
import SearchBar from "../components/common/SearchBar.tsx";
import DataTable from "../components/common/DataTable.tsx";
import SortableHeader from "../components/common/SortableHeader.tsx";
import ActionButtons from "../components/common/ActionButtons.tsx";
import {formatDate, formatName} from "../utils/formatters.ts";
import Pagination from "../components/common/Pagination.tsx";
import type {BatchSortField} from "../types/batches.ts";
import {deleteBatch, getBatches} from "../api/batches.ts";
import BatchInfoModal from "../components/batches/BatchInfoModal.tsx";
import BatchCreateModal from "../components/batches/BatchCreateModal.tsx";
import BatchUpdateModal from "../components/batches/BatchUpdateModal.tsx";
import BatchCreateMatrixModal from "../components/batches/BatchCreateMatrixModal.tsx";

export default function BatchesPage() {
    const queryClient = useQueryClient();
    const [searchParams, setSearchParams] = useSearchParams();

    // Generic State
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<BatchSortField>('created_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    // Modal State
    const isCreateModalOpen = searchParams.get('create') === 'true';
    const isCreateFastModalOpen = searchParams.get('create-fast') === 'true';
    const [infoId, setInfoId] = useState<number | null>(null);
    const [updateBatch, setUpdateBatch] = useState<{ id: number, name: string } | null>(null);

    // Hook for Table Sizing
    const tableContainerRef = useRef<HTMLDivElement | null>(null);
    const {pageSize} = useAutoPageSize(tableContainerRef);

    // Query Data
    const {data, isLoading, isError, isPlaceholderData} = useQuery({
        queryKey: ['batches', {page, pageSize, sortBy, sortDir, appliedSearch}],
        queryFn: () => getBatches(page, pageSize, sortBy, sortDir, appliedSearch),
        placeholderData: keepPreviousData,
    });

    const batches = data?.batches || [];
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
        const typedField = field as BatchSortField;
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
        mutationFn: ({id}: { id: number, name: string }) => deleteBatch(id),
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

            <BatchCreateModal
                isOpen={isCreateModalOpen}
                onClose={() => {
                    searchParams.delete('create');
                    setSearchParams(searchParams);
                }}
                onSuccessSubmit={(name, id) => showToast(`${name} created successfully!`, "success", id)}
            />

            <BatchCreateMatrixModal
                isOpen={isCreateFastModalOpen}
                onClose={() => {
                    searchParams.delete('create-fast');
                    setSearchParams(searchParams);
                }}
                onSuccessSubmit={(name, id) => showToast(`${name} created successfully!`, "success", id)}
            />

            <BatchInfoModal batchId={infoId} onClose={() => setInfoId(null)}/>

            {updateBatch && (
                <BatchUpdateModal
                    config={updateBatch}
                    onClose={() => setUpdateBatch(null)}
                    onSuccess={(msg, id) => showToast(msg, "success", id)}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <h1 className="text-3xl font-bold text-gray-900">Batches</h1>
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
            </div>

            {isError && (
                <div className="text-red-500 mb-4 p-4 bg-red-50 rounded-md border border-red-200">
                    Failed to load batches. Please make sure the backend is running.
                </div>
            )}

            <DataTable
                containerRef={tableContainerRef}
                headers={
                    <>
                        <SortableHeader label="Name" field="name" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Total Experiments" field="total_experiment_amount" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Queued Experiments" field="queued_experiment_amount"
                                        currentSortBy={sortBy} currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Running Experiments" field="running_experiment_amount"
                                        currentSortBy={sortBy} currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Finished Experiments" field="finished_experiment_amount"
                                        currentSortBy={sortBy} currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Failed Experiments" field="failed_experiment_amount"
                                        currentSortBy={sortBy} currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Created At" field="created_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                        <SortableHeader label="Updated At" field="updated_at" currentSortBy={sortBy}
                                        currentSortDir={sortDir} onSort={handleSort}/>
                    </>
                }
            >
                {isLoading ? (
                    <tr>
                        <td colSpan={5} className="text-center py-10 text-gray-500">Loading batches...</td>
                    </tr>
                ) : batches.length === 0 ? (
                    <tr>
                        <td colSpan={5} className="text-center py-10 text-gray-500">No batches found.</td>
                    </tr>
                ) : (
                    batches.map((batch) => (
                        <tr key={batch.id}
                            className={`hover:bg-gray-50 transition-opacity ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                                <ActionButtons
                                    onInfo={() => setInfoId(batch.id)}
                                    onEdit={() => setUpdateBatch({id: batch.id!, name: batch.name || ''})}
                                    onDelete={() => {
                                        const listName = batch.name || 'Unnamed Batch';
                                        if (window.confirm(`Are you sure you want to delete ${listName}?`)) {
                                            deleteMutation.mutate({id: batch.id, name: listName});
                                        }
                                    }}
                                    deleteDisabled={deleteMutation.isPending}
                                />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(batch.name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{batch.total_experiment_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{batch.queued_experiment_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{batch.running_experiment_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{batch.finished_experiment_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{batch.failed_experiment_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(batch.created_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(batch.updated_at)}</td>
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