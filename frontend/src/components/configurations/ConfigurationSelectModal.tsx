import {useRef, useState} from 'react';
import {keepPreviousData, useQuery} from '@tanstack/react-query';
import {getConfigurations} from '../../api/configurations';
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
} from '../../utils/formatters';
import type {SortDirection} from '../../types/common';
import type {ConfigurationSingleGetResponseDTO, ConfigurationSortField} from '../../types/configurations';
import {CheckIcon, InformationCircleIcon} from '@heroicons/react/24/outline';

import SearchBar from '../common/SearchBar';
import FilterSelector, {type FilterCategory} from '../common/FilterSelector';
import DataTable from '../common/DataTable';
import SortableHeader from '../common/SortableHeader';
import Pagination from '../common/Pagination';
import ConfigurationInfoModal from './ConfigurationInfoModal';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (id: number, data: ConfigurationSingleGetResponseDTO) => void;
}

const FILTER_CATEGORIES: FilterCategory[] = [
    {
        id: 'solver_type',
        label: 'Solver Type',
        options: [
            {label: 'Hexaly', value: 'hexaly'},
            {label: 'Cplex Medicine', value: 'cplex_medicine'},
            {label: 'Cplex Perfumes', value: 'cplex_perfumes'}
        ]
    }
];

export default function ConfigurationSelectModal({isOpen, onClose, onSelect}: Props) {
    const tableContainerRef = useRef<HTMLDivElement>(null);

    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState<ConfigurationSortField>('updated_at');
    const [sortDir, setSortDir] = useState<SortDirection>('desc');
    const [searchInput, setSearchInput] = useState('');
    const [appliedSearch, setAppliedSearch] = useState('');
    const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

    const [infoConfigId, setInfoConfigId] = useState<number | null>(null);

    const pageSize = 5;

    const {data, isLoading, isPlaceholderData} = useQuery({
        queryKey: ['configurations_select', {
            page,
            pageSize,
            sortBy,
            sortDir,
            appliedSearch,
            types: selectedFilters.solver_type
        }],
        queryFn: () => getConfigurations(page, pageSize, sortBy, sortDir, appliedSearch, selectedFilters.solver_type),
        placeholderData: keepPreviousData,
        enabled: isOpen,
    });

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

    if (!isOpen) return null;

    return (
        <>
            {/* Main Selection Modal */}
            <div className="fixed inset-0 z-70 flex items-center justify-center p-6 bg-black/40 backdrop-blur-[1px]"
                 onClick={onClose}>
                <div
                    className="bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-5xl flex flex-col h-175"
                    onClick={e => e.stopPropagation()}>

                    {/* Header */}
                    <div
                        className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0 bg-gray-50 rounded-t-lg">
                        <h2 className="text-xl font-bold text-gray-900">Select Configuration</h2>
                        <button onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-200 transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>

                    {/* Controls */}
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
                        {isPlaceholderData &&
                            <span className="text-sm text-gray-500 animate-pulse ml-4">Updating...</span>}
                    </div>

                    {/* Table Area */}
                    <div className="flex-1 min-h-0 p-4 bg-gray-50/50">
                        <DataTable
                            containerRef={tableContainerRef}
                            headers={
                                <>
                                    <SortableHeader label="Name" field="name" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
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
                                    <SortableHeader label="Dispensing Time" field="dispensing_time"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Batch Size" field="batch_size" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Warmup" field="warmup" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Dispense rate" field="dispense_rate" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Mover Speed" field="mover_speed" currentSortBy={sortBy}
                                                    currentSortDir={sortDir} onSort={handleSort}/>
                                    <SortableHeader label="Viscosity Exponent" field="viscosity_exponent"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Mixer Primary Time" field="mixer_primary_time"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
                                    <SortableHeader label="Mixer Final Time" field="mixer_final_time"
                                                    currentSortBy={sortBy} currentSortDir={sortDir}
                                                    onSort={handleSort}/>
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
                                    <td colSpan={17} className="text-center py-10 text-gray-500">Loading
                                        configurations...
                                    </td>
                                </tr>
                            ) : !data?.configurations?.length ? (
                                <tr>
                                    <td colSpan={17} className="text-center py-10 text-gray-500">No configurations
                                        found.
                                    </td>
                                </tr>
                            ) : (
                                data.configurations.map((config: ConfigurationSingleGetResponseDTO) => (
                                    <tr key={config.id}
                                        className={`hover:bg-blue-50 transition-all ${isPlaceholderData ? 'opacity-50' : 'opacity-100'}`}>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm flex gap-2">
                                            <button
                                                onClick={() => setInfoConfigId(config.id)}
                                                className="text-green-800 hover:text-green-700 bg-green-50 p-1.5 rounded border border-green-700 shadow hover:shadow-md transition-all"
                                                title="View Details"
                                            >
                                                <InformationCircleIcon className="w-5 h-5"/>
                                            </button>
                                            <button
                                                onClick={() => onSelect(config.id, config)}
                                                className="text-blue-800 hover:text-blue-700 bg-blue-50 p-1.5 rounded border border-blue-700 shadow hover:shadow-md transition-all"
                                                title="Select this configuration"
                                            >
                                                <CheckIcon className="w-5 h-5"/>
                                            </button>
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
                    </div>

                    <Pagination
                        page={page}
                        totalPages={data?.total || 1}
                        onPageChange={setPage}
                        isDisabled={isLoading || isPlaceholderData}
                    />
                </div>
            </div>

            <ConfigurationInfoModal
                configId={infoConfigId}
                onClose={() => setInfoConfigId(null)}
            />
        </>
    );
}