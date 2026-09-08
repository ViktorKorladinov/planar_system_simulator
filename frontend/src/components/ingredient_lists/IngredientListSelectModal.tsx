import {useRef, useState} from 'react';
import {keepPreviousData, useQuery} from '@tanstack/react-query';
import {getIngredientLists} from '../../api/ingredient_lists';
import {formatDate, formatIngredientListType, formatName} from '../../utils/formatters';
import type {IngredientListSortField} from '../../types/ingredient_lists';
import type {SortDirection} from '../../types/common';
import {CheckIcon, InformationCircleIcon} from '@heroicons/react/24/outline';

import SearchBar from '../common/SearchBar';
import FilterSelector, {type FilterCategory} from '../common/FilterSelector';
import DataTable from '../common/DataTable';
import SortableHeader from '../common/SortableHeader';
import Pagination from '../common/Pagination';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (id: number) => void;
    onInfo?: (id: number) => void;
}

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'ingredient_list_type',
        label: 'Ingredient List Type',
        options: [
            {label: 'Medicine', value: 'medicine'},
            {label: 'Perfume', value: 'perfume'}
        ]
    }
];

export default function IngredientListSelectModal({isOpen, onClose, onSelect, onInfo}: Props) {
    const tableContainerRef = useRef<HTMLDivElement>(null);

    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<IngredientListSortField>('updated_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
    const pageSize = 5;

    const {data, isLoading, isPlaceholderData} = useQuery({
        queryKey: ['ingredient_lists_select', {
            page,
            pageSize,
            sortBy,
            sortDir,
            appliedSearch,
            types: selectedFilters.ingredient_list_type
        }],
        queryFn: () => getIngredientLists(page, pageSize, sortBy, sortDir, appliedSearch, selectedFilters.ingredient_list_type),
        placeholderData: keepPreviousData,
        enabled: isOpen,
    });

    const handleSort = (field: string) => {
        const typedField = field as IngredientListSortField;
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
        <div className="fixed inset-0 z-70 flex items-center justify-center p-6 bg-black/40 backdrop-blur-[1px]"
             onClick={onClose}>
            <div className="bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-5xl flex flex-col h-175"
                 onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div
                    className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0 bg-gray-50 rounded-t-lg">
                    <h2 className="text-xl font-bold text-gray-900">Select Ingredient List</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-200 transition-colors">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>

                {/* Controls (Search & Filter) */}
                <div className="p-4 border-b border-gray-200 shrink-0 flex items-center space-x-2">
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
                    {isPlaceholderData && <span className="text-sm text-gray-500 animate-pulse ml-4">Updating...</span>}
                </div>

                {/* Table Area */}
                <div className="flex-1 min-h-0 p-4 bg-gray-50/50">
                    <DataTable
                        containerRef={tableContainerRef}
                        headers={
                            <>
                                <SortableHeader label="Name" field="name" currentSortBy={sortBy}
                                                currentSortDir={sortDir} onSort={handleSort}/>
                                <SortableHeader label="Type" field="type" currentSortBy={sortBy}
                                                currentSortDir={sortDir} onSort={handleSort}/>
                                <SortableHeader label="Ingredients" field="ingredient_amount" currentSortBy={sortBy}
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
                                <td colSpan={6} className="text-center py-10 text-gray-500">Loading ingredient
                                    lists...
                                </td>
                            </tr>
                        ) : !data?.ingredient_lists.length ? (
                            <tr>
                                <td colSpan={6} className="text-center py-10 text-gray-500">No ingredient lists found.
                                </td>
                            </tr>
                        ) : (
                            data.ingredient_lists.map(list => (
                                <tr key={list.id}
                                    className={`hover:bg-blue-50 transition-all ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>

                                    <td className="px-4 py-3 whitespace-nowrap text-sm flex gap-2">
                                        <button
                                            onClick={() => onInfo && onInfo(list.id)}
                                            className="text-green-800 hover:text-green-700 bg-green-50 p-1.5 rounded border border-green-700 shadow hover:shadow-md transition-all"
                                            title="View Details"
                                        >
                                            <InformationCircleIcon className="w-5 h-5"/>
                                        </button>
                                        <button
                                            onClick={() => onSelect(list.id)}
                                            className="text-blue-800 hover:text-blue-700 bg-blue-50 p-1.5 rounded border border-blue-700 shadow hover:shadow-md transition-all"
                                            title="Select this list"
                                        >
                                            <CheckIcon className="w-5 h-5"/>
                                        </button>
                                    </td>

                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{formatName(list.name)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatIngredientListType(list.type)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{list.ingredient_amount}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(list.created_at)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(list.updated_at)}</td>
                                </tr>
                            ))
                        )}
                    </DataTable>
                </div>

                {/* Footer Pagination */}
                <Pagination
                    page={page}
                    totalPages={data?.total || 1}
                    onPageChange={setPage}
                    isDisabled={isLoading || isPlaceholderData}
                />
            </div>
        </div>
    );
}