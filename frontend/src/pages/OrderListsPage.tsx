import {keepPreviousData, useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {useSearchParams} from "react-router-dom";
import {useRef, useState} from "react";
import type {OrderListSingleGetResponseDTO, OrderListSortField} from "../types/order_lists.ts";
import type {SortDirection, ToastMessage} from "../types/common.ts";
import {useAutoPageSize} from "../hooks/useAutoPageSize.ts";
import {deleteOrderList, getOrderLists} from "../api/order_lists.ts";
import ToastNotification from "../components/common/ToastNotification.tsx";
import SearchBar from "../components/common/SearchBar.tsx";
import DataTable from "../components/common/DataTable.tsx";
import SortableHeader from "../components/common/SortableHeader.tsx";
import ActionButtons from "../components/common/ActionButtons.tsx";
import Pagination from "../components/common/Pagination.tsx";
import {formatDate, formatName, formatOrderListType} from "../utils/formatters.ts";
import OrderListInfoModal from "../components/order_lists/OrderListInfoModal.tsx";
import OrderListCreateModal from "../components/order_lists/OrderListCreateModal.tsx";
import OrderListUpdateModal from "../components/order_lists/OrderListUpdateModal.tsx";
import FilterSelector, {type FilterCategory} from "../components/common/FilterSelector.tsx";

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'order_list_type',
        label: 'Order List Type',
        options: [
            {label: 'Medicine', value: 'medicine'},
            {label: 'Perfume', value: 'perfume'}
        ]
    }
];

export default function OrderListsPage() {
    const queryClient = useQueryClient();
    const [searchParams, setSearchParams] = useSearchParams();

    // Generic State
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<OrderListSortField>('created_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    // Modal State
    const isCreateModalOpen = searchParams.get('create') === 'true';
    const [infoId, setInfoId] = useState<number | null>(null);
    const [updateOrderList, setUpdateOrderList] = useState<{ id: number, name: string } | null>(null);
    const [copyData, setCopyData] = useState<OrderListSingleGetResponseDTO | null>(null);

    // Hook for Table Sizing
    const tableContainerRef = useRef<HTMLDivElement | null>(null);
    const {pageSize} = useAutoPageSize(tableContainerRef);

    // Filter Initialization
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    // Query Data
    const {data, isLoading, isError, isPlaceholderData} = useQuery({
        queryKey: ['order_lists', {
            page,
            pageSize,
            sortBy,
            sortDir,
            appliedSearch,
            types: selectedFilters.order_list_type
        }],
        queryFn: () => getOrderLists(page, pageSize, sortBy, sortDir, appliedSearch, selectedFilters.order_list_type),
        placeholderData: keepPreviousData,
    });

    const orderLists = data?.order_lists || [];
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
        const typedField = field as OrderListSortField;
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
        searchParams.delete('upload');
        setSearchParams(searchParams);
        setCopyData(null);
    };

    const deleteMutation = useMutation({
        mutationFn: ({id}: { id: number, name: string }) => deleteOrderList(id),
        onSuccess: async (_data, variables) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['order_lists']}),
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

            <OrderListCreateModal
                isOpen={isCreateModalOpen}
                initialData={copyData}
                onClose={closeCreateModal}
                onSuccessSubmit={(name, id) => showToast(`${name} created successfully!`, "success", id)}
            />

            <OrderListInfoModal
                orderListId={infoId}
                onClose={() => setInfoId(null)}
                onCopyCreate={(data) => {
                    setInfoId(null);
                    setCopyData(data);
                    openCreateModal();
                }}
            />

            {updateOrderList && (
                <OrderListUpdateModal
                    config={updateOrderList}
                    onClose={() => setUpdateOrderList(null)}
                    onSuccess={(msg, id) => showToast(msg, "success", id)}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {/* Header */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <h1 className="text-3xl font-bold text-gray-900">Order Lists</h1>
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
                    Failed to load order lists. Please make sure the backend is running.
                </div>
            )}

            <DataTable
                containerRef={tableContainerRef}
                headers={
                    <>
                        <SortableHeader label="Name" field="name" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Type" field="type" currentSortBy={sortBy} currentSortDir={sortDir}
                                        onSort={handleSort}/>
                        <SortableHeader label="Order Amount" field="order_amount" currentSortBy={sortBy}
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
                        <td colSpan={5} className="text-center py-10 text-gray-500">Loading order lists...</td>
                    </tr>
                ) : orderLists.length === 0 ? (
                    <tr>
                        <td colSpan={5} className="text-center py-10 text-gray-500">No order lists found.</td>
                    </tr>
                ) : (
                    orderLists.map((list) => (
                        <tr key={list.id}
                            className={`hover:bg-gray-50 transition-opacity ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                            <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                                <ActionButtons
                                    onInfo={() => setInfoId(list.id)}
                                    onEdit={() => setUpdateOrderList({id: list.id!, name: list.name || ''})}
                                    onDelete={() => {
                                        const listName = list.name || 'Unnamed Order List';
                                        if (window.confirm(`Are you sure you want to delete ${listName}?`)) {
                                            deleteMutation.mutate({id: list.id, name: listName});
                                        }
                                    }}
                                    deleteDisabled={deleteMutation.isPending}
                                />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(list.name)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatOrderListType(list.type)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{list.order_amount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(list.created_at)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(list.updated_at)}</td>
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