import {useRef, useState} from 'react';
import {keepPreviousData, useQuery, useQueryClient} from '@tanstack/react-query';
import {getLayout, getLayouts} from '../../api/layouts';
import {formatDate, formatIngredientListType, formatName} from '../../utils/formatters';
import type {SortDirection} from '../../types/common';
import type {LayoutSingleGetResponseDTO, LayoutSortField, LayoutSummaryResponseDTO} from '../../types/layouts';
import {CheckIcon, InformationCircleIcon} from '@heroicons/react/24/outline';

import SearchBar from '../common/SearchBar';
import FilterSelector, {type FilterCategory} from '../common/FilterSelector';
import DataTable from '../common/DataTable';
import SortableHeader from '../common/SortableHeader';
import Pagination from '../common/Pagination';
import LayoutInfoModal from './LayoutInfoModal';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (id: number, data: LayoutSingleGetResponseDTO) => void;
}

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'type',
        label: 'Layout Type',
        options: [
            {label: 'Line', value: 'line'},
            {label: 'Double Line', value: 'double_line'},
            {label: 'Ring', value: 'ring'},
            {label: 'Custom', value: 'custom'}
        ]
    }
];

export default function LayoutSelectModal({isOpen, onClose, onSelect}: Props) {
    const tableContainerRef = useRef<HTMLDivElement>(null);
    const queryClient = useQueryClient();

    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<LayoutSortField>('updated_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    const [infoLayoutId, setInfoLayoutId] = useState<number | null>(null);

    const pageSize = 5;

    const {data, isLoading, isPlaceholderData} = useQuery({
        queryKey: ['layouts_select', {page, pageSize, sortBy, sortDir, appliedSearch, types: selectedFilters.type}],
        queryFn: () => getLayouts(page, pageSize, sortBy, sortDir, appliedSearch, selectedFilters.type),
        placeholderData: keepPreviousData,
        enabled: isOpen,
    });

    const handleSort = (field: string) => {
        const typedField = field as LayoutSortField;
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

    if (!isOpen) return null;

    return (
        <>
            <div className="fixed inset-0 z-70 flex items-center justify-center p-6 bg-black/40 backdrop-blur-[1px]"
                 onClick={onClose}>
                <div
                    className="bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-6xl flex flex-col h-175"
                    onClick={e => e.stopPropagation()}>

                    <div
                        className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0 bg-gray-50 rounded-t-lg">
                        <h2 className="text-xl font-bold text-gray-900">Select Layout</h2>
                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-200 transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>

                    <div className="p-4 border-b border-gray-200 shrink-0 flex items-center space-x-2">
                        <SearchBar value={searchInput} onChange={setSearchInput} onSearch={() => {
                            setAppliedSearch(searchInput);
                            setPage(1);
                        }}/>
                        <FilterSelector categories={FILTER_CATEGORIES} selectedValues={selectedFilters}
                                        onChange={handleFilterChange}/>
                        {isPlaceholderData &&
                            <span className="text-sm text-gray-500 animate-pulse ml-4">Updating...</span>}
                    </div>

                    <div className="flex-1 min-h-0 p-4 bg-gray-50/50">
                        <DataTable
                            containerRef={tableContainerRef}
                            headers={
                                <>
                                    <SortableHeader label="Name" field="name" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Type" field="type" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Ingredients Type" field="ingredient_list_type"
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
                                    <SortableHeader label="Created At" field="created_at" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Updated At" field="updated_at" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                </>
                            }
                        >
                            {isLoading ? (
                                <tr>
                                    <td colSpan={9} className="text-center py-10 text-gray-500">Loading layouts...</td>
                                </tr>
                            ) : !data?.layouts?.length ? (
                                <tr>
                                    <td colSpan={9} className="text-center py-10 text-gray-500">No layouts found.</td>
                                </tr>
                            ) : (
                                data.layouts.map((layout: LayoutSummaryResponseDTO) => (
                                    <tr key={layout.id}
                                        className={`hover:bg-blue-50 transition-all ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm flex gap-2">
                                            <button
                                                onClick={() => setInfoLayoutId(layout.id)}
                                                className="text-green-800 hover:text-green-700 bg-green-50 p-1.5 rounded border border-green-700 shadow hover:shadow-md transition-all"
                                                title="View Details"
                                            >
                                                <InformationCircleIcon className="w-5 h-5"/>
                                            </button>
                                            <button
                                                onClick={async () => {
                                                    const fullLayoutData = await queryClient.fetchQuery({
                                                        queryKey: ['layout', layout.id],
                                                        queryFn: () => getLayout(layout.id)
                                                    });
                                                    onSelect(layout.id, fullLayoutData);
                                                }}
                                                className="text-blue-800 hover:text-blue-700 bg-blue-50 p-1.5 rounded border border-blue-700 shadow hover:shadow-md transition-all"
                                                title="Select this layout"
                                            >
                                                <CheckIcon className="w-5 h-5"/>
                                            </button>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(layout.name)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">{layout.type.replace('_', ' ')}</td>

                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {layout.ingredient_list_type ? formatIngredientListType(layout.ingredient_list_type) : '-'}
                                        </td>

                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{layout.tile_amount ?? '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{layout.interface_amount ?? '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{layout.dispenser_amount ?? '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(layout.created_at)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(layout.updated_at)}</td>
                                    </tr>
                                ))
                            )}
                        </DataTable>
                    </div>

                    <Pagination page={page} totalPages={data?.total || 1} onPageChange={setPage}
                                isDisabled={isLoading || isPlaceholderData}/>
                </div>
            </div>

            <LayoutInfoModal layoutId={infoLayoutId} onClose={() => setInfoLayoutId(null)}/>
        </>
    );
}