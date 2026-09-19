import {useEffect, useRef, useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {getExperiment} from '../../api/experiments';
import type {ExperimentSingleGetResponseDTO} from '../../types/experiments';
import {formatSolverType} from '../../utils/formatters';
import {
    ArrowPathIcon,
    ArrowTopRightOnSquareIcon,
    CircleStackIcon,
    DocumentDuplicateIcon,
    FunnelIcon,
    InformationCircleIcon,
    PlusCircleIcon,
    TruckIcon,
    XCircleIcon
} from '@heroicons/react/24/outline';
import IngredientListInfoModal from '../ingredient_lists/IngredientListInfoModal';

interface Props {
    experimentId: number | null;
    onClose: () => void;
    onCopyCreate?: (data: ExperimentSingleGetResponseDTO) => void;
}

const getDispenserInitials = (types: string[]) => {
    if (!types || !Array.isArray(types) || types.length === 0) return '';
    const result = [...types].sort((a, b) => a.localeCompare(b)).slice(0, 5).map(t => (typeof t === 'string' && t.length > 0) ? t.charAt(0).toUpperCase() : '').filter(Boolean).join(',')
    if (types.length > 5) return result + '...'
    return result
};

export default function ExperimentInfoModal({experimentId, onClose, onCopyCreate}: Props) {
    const [activeTab, setActiveTab] = useState<'configuration' | 'layout' | 'order_list' | 'simulation' | 'gantt'>('configuration');
    const [infoIngredientListId, setInfoIngredientListId] = useState<number | null>(null);
    const [zoom, setZoom] = useState(1);
    const [hoveredType, setHoveredType] = useState<string | null>(null);
    const [selectedGanttIndex, setSelectedGanttIndex] = useState(0);

    const SIMULATOR_URL = import.meta.env.VITE_SIMULATOR_URL || 'http://localhost:3000';
    const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

    const {data, isLoading, isError} = useQuery({
        queryKey: ['experiment_details', experimentId],
        queryFn: () => getExperiment(experimentId!),
        enabled: !!experimentId,
    });

    const {data: simulationData, isLoading: isSimLoading} = useQuery({
        queryKey: ['simulation_details', experimentId],
        queryFn: async () => {
            const response = await fetch(`${API_BASE_URL}/simulations/${experimentId}`);
            if (!response.ok) throw new Error('Simulation not found');
            return response.json();
        },
        enabled: !!experimentId && activeTab === 'gantt' && data?.status === 'finished',
    });

    const ganttNames: string[] = simulationData?.gantts?.names || [];
    const activeGanttName = ganttNames[selectedGanttIndex] || ganttNames[0] || '';

    const getGanttPlotUrl = (name: string) => {
        if (!name) return '';
        if (simulationData?.gantts?.api_plot_url) {
            let url = simulationData.gantts.api_plot_url.replace(/\/$/, '');
            if (url.includes('backend:8000')) {
                url = url.replace('backend:8000', 'localhost:8000');
            }
            return `${url}/${name}`;
        }
        return `${API_BASE_URL}/simulations/${experimentId}/plots/${name}`;
    };

    const currentGanttUrl = getGanttPlotUrl(activeGanttName);

    const formatGanttName = (name: string) => {
        return name
            .replace(/_graph$/, '')
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const handleClose = () => {
        setActiveTab('configuration');
        setZoom(1);
        setHoveredType(null);
        setSelectedGanttIndex(0);
        onClose();
    };

    const layoutTiles = data?.layout?.tiles || [];
    const dimensions = {
        width: Math.max(0, ...layoutTiles.map(t => t.x)) + 1 || 3,
        height: Math.max(0, ...layoutTiles.map(t => t.y)) + 1 || 3
    };

    const activeIngredients = Array.from(new Set(
        layoutTiles.flatMap(t => t.dispensed_types || [])
    )).sort();

    const gridContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const container = gridContainerRef.current;
        if (!container || activeTab !== 'layout' || layoutTiles.length === 0) return;

        const updateZoom = () => {
            const padding = 32;
            const availableW = container.clientWidth - padding;
            const availableH = container.clientHeight - padding;

            if (availableW <= 0 || availableH <= 0) return;

            const neededW = dimensions.width * 80 + Math.max(0, dimensions.width - 1) * 4;
            const neededH = dimensions.height * 80 + Math.max(0, dimensions.height - 1) * 4;

            if (neededW > 0 && neededH > 0) {
                setZoom(Math.max(0.1, parseFloat(Math.min(1, availableW / neededW, availableH / neededH).toFixed(2))));
            }
        };

        const observer = new ResizeObserver(() => updateZoom());
        observer.observe(container);

        updateZoom();

        return () => observer.disconnect();
    }, [activeTab, layoutTiles.length, dimensions.width, dimensions.height]);

    if (!experimentId) return null;

    const activeIngredientListId = data?.ingredient_list_id;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px]" onClick={handleClose}></div>

            <div
                className={`relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full flex flex-col max-h-[96vh] transition-all duration-200 ${
                    (activeTab === 'simulation' || activeTab === 'gantt') ? 'max-w-[96vw] h-[92vh]' : 'max-w-6xl h-225'
                }`}>

                {/* Header */}
                <div
                    className="px-6 border-b border-gray-200 flex justify-between items-center shrink-0 bg-white rounded-t-lg h-16 gap-6">
                    <div className="flex-1 min-w-0 flex items-center text-xl font-bold text-gray-900 gap-2">
                        <span className="shrink-0">Experiment Details</span>
                        {data?.name && (
                            <>
                                <span className="shrink-0">-</span>
                                <span className="truncate" title={data.name}>
                            {data.name}
                        </span>
                            </>
                        )}
                    </div>
                    <div className="flex items-center h-full shrink-0 gap-4">

                        {/* Tabs */}
                        <div className="flex space-x-6 h-full">
                            {[
                                {id: 'configuration', label: 'Configuration'},
                                {id: 'layout', label: 'Layout'},
                                {id: 'order_list', label: 'Order List'},
                                {id: 'simulation', label: 'Simulation'},
                                {id: 'gantt', label: 'Gantt Chart'}
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                    className={`relative h-full flex items-center px-2 text-sm font-medium whitespace-nowrap transition-colors ${
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

                        {activeTab === 'simulation' && data?.status === 'finished' && (
                            <a
                                href={`${SIMULATOR_URL}/${experimentId}/simulator`}
                                target="_blank"
                                rel="noreferrer"
                                className="text-gray-500 hover:text-gray-800 px-2.5 py-1.5 rounded-md hover:bg-gray-100 transition-colors flex items-center gap-1.5 text-xs font-medium border border-gray-200 shadow-xs"
                                title="Open simulator in full window"
                            >
                                <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                <span className="hidden sm:inline">Fullscreen</span>
                            </a>
                        )}

                        {activeTab === 'gantt' && data?.status === 'finished' && currentGanttUrl && (
                            <a
                                href={currentGanttUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="text-gray-500 hover:text-gray-800 px-2.5 py-1.5 rounded-md hover:bg-gray-100 transition-colors flex items-center gap-1.5 text-xs font-medium border border-gray-200 shadow-xs"
                                title="Open Gantt chart in full window"
                            >
                                <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                <span className="hidden sm:inline">Fullscreen</span>
                            </a>
                        )}

                        <button onClick={handleClose}
                                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-md hover:bg-gray-100 transition-colors shrink-0"
                                title="Close">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 min-h-0 bg-gray-50 relative flex flex-col">
                    {isLoading ? (
                        <div className="h-full flex items-center justify-center text-gray-500">Loading details...</div>
                    ) : isError || !data ? (
                        <div className="h-full flex items-center justify-center text-red-500">Failed to load experiment
                            details.</div>
                    ) : (
                        <>
                            {/* CONFIGURATION TAB */}
                            <div className={activeTab === 'configuration' ? 'p-6 overflow-y-auto flex-1' : 'hidden'}>
                                <div className="max-w-4xl mx-auto space-y-6 pb-8">
                                    <div
                                        className="bg-white p-4 rounded-md border border-gray-200 shadow-sm grid grid-cols-1 gap-4">
                                        <div className="col-span-2 sm:col-span-1">
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Configuration
                                                Name</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 text-sm min-h-9.5 flex items-center">
                                                {data.configuration.name ||
                                                    <span className="text-gray-400 italic">Unnamed</span>}
                                            </div>
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Solver
                                                Type</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 text-sm min-h-9.5 flex items-center">
                                                {formatSolverType(data.configuration.solver_type)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">General
                                            Parameters</h3>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Interface
                                                Time (s)</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.interface_time}</div>
                                            </div>
                                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Dispensing
                                                Time (s)</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.dispensing_time}</div>
                                            </div>
                                            <div><label
                                                className="block text-xs font-medium text-gray-500 mb-1">Movers</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.mover_amount}</div>
                                            </div>
                                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Time
                                                Limit (s)</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.time_limit}</div>
                                            </div>
                                            <div className="col-span-2"><label
                                                className="block text-xs font-medium text-gray-500 mb-1">Processes</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.process_amount}</div>
                                            </div>
                                        </div>
                                    </div>

                                    {data.configuration.solver_type === 'cplex_medicine' && (
                                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                                Parameters</h3>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Batch
                                                    Size</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.batch_size ?? '-'}</div>
                                                </div>
                                                <div><label
                                                    className="block text-xs font-medium text-gray-500 mb-1">Warmup</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.warmup ? 'Yes' : 'No'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {data.configuration.solver_type === 'cplex_perfumes' && (
                                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                                Parameters</h3>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Dispense
                                                    Rate (s/ml)</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.dispense_rate ?? '-'}</div>
                                                </div>
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Viscosity
                                                    Exponent</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.viscosity_exponent ?? '-'}</div>
                                                </div>
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Mover
                                                    Speed (s per tile)</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.mover_speed ?? '-'}</div>
                                                </div>
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer
                                                    Primary Time (s)</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.mixer_primary_time ?? '-'}</div>
                                                </div>
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer
                                                    Final Time (s)</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.mixer_final_time ?? '-'}</div>
                                                </div>
                                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Capper
                                                    Time (s)</label>
                                                    <div
                                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data.configuration.capper_time ?? '-'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Layout Tab */}
                            <div className={activeTab === 'layout' ? 'p-6 flex-1 flex gap-6 min-h-0' : 'hidden'}>
                                {/* Left Side */}
                                <div className="w-56 flex flex-col gap-4 shrink-0 h-full">
                                    <div
                                        className="bg-white border border-gray-200 rounded-md shadow-sm p-4 flex flex-col gap-4 shrink-0">
                                        <div><label
                                            className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Layout
                                            Name</label>
                                            <div className="text-sm font-medium text-gray-900">{data.layout.name ||
                                                <span className="text-gray-400 italic">Unnamed</span>}</div>
                                        </div>
                                        <div><label
                                            className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Type</label>
                                            <div
                                                className="text-sm font-medium text-gray-800 capitalize">{data.layout.type.replace('_', ' ')}</div>
                                        </div>
                                        <div className="border-t border-gray-100 pt-3 mt-1">
                                            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Layout
                                                Statistics</h3>
                                            <div className="grid grid-cols-2 gap-y-2 text-sm text-gray-600">
                                                <div className="flex items-center gap-1.5" title="Interface Tiles">
                                                    <div className="text-blue-500"><TruckIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'interface').length}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5" title="Dispenser Tiles">
                                                    <div className="text-orange-500"><FunnelIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'dispenser').length}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5" title="Mixer Tiles">
                                                    <div className="text-green-500"><ArrowPathIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'mixer').length}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5" title="Capper Tiles">
                                                    <div className="text-red-500"><CircleStackIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'capper').length}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5" title="Empty Tiles">
                                                    <div className="text-gray-400"><PlusCircleIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'empty').length}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5" title="Blocked Tiles">
                                                    <div className="text-gray-800"><XCircleIcon className="w-4 h-4"/>
                                                    </div>
                                                    <span
                                                        className="font-medium">{layoutTiles.filter(t => t.type === 'blocked').length}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div
                                        className="flex flex-col flex-1 min-h-0 bg-white border border-gray-200 rounded-md shadow-sm overflow-hidden">
                                        <div
                                            className="p-3 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
                                            <span className="font-semibold text-sm text-gray-800">Ingredients</span>
                                            {activeIngredientListId && (
                                                <button onClick={() => setInfoIngredientListId(activeIngredientListId)}
                                                        className="p-1 text-green-700 bg-green-50 hover:bg-green-100 border border-green-700 rounded transition-colors shadow-sm"
                                                        title="View Ingredient List Details"><InformationCircleIcon
                                                    className="w-4 h-4"/></button>
                                            )}
                                        </div>
                                        <div
                                            className="bg-white border-b border-gray-100 p-2 text-xs font-medium text-center text-gray-600 truncate">
                                            {data.layout.ingredient_list?.name || (activeIngredientListId ? `Linked List #${activeIngredientListId}` : 'No list attached')}
                                        </div>
                                        <div className="flex-1 overflow-y-auto p-2 space-y-1">
                                            {activeIngredients.map(t => (
                                                <div key={t} onMouseEnter={() => setHoveredType(t)}
                                                     onMouseLeave={() => setHoveredType(null)}
                                                     className="flex items-center justify-between p-2.5 bg-gray-50 border border-gray-200 rounded text-sm hover:bg-gray-100 transition-colors">
                                                    <span className="truncate flex-1 font-medium text-gray-700"
                                                          title={t}>{t}</span>
                                                </div>
                                            ))}
                                            {activeIngredients.length === 0 &&
                                                <p className="text-xs text-gray-400 text-center mt-4 p-2">No ingredients
                                                    configured.</p>}
                                        </div>
                                    </div>
                                </div>

                                {/* Middle Grid */}
                                <div
                                    className="flex-1 flex flex-col bg-white border border-gray-200 rounded-md shadow-sm relative overflow-hidden">
                                    <div
                                        className="absolute top-3 right-3 z-20 flex items-center bg-white border border-gray-200 rounded-md shadow-sm opacity-90 hover:opacity-100 transition-opacity">
                                        <button onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}
                                                className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-l-md">
                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24"
                                                 stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                      d="M20 12H4"/>
                                            </svg>
                                        </button>
                                        <span
                                            className="px-2 text-xs font-medium text-gray-600 border-x border-gray-200 w-12 text-center">{Math.round(zoom * 100)}%</span>
                                        <button onClick={() => setZoom(z => Math.min(2.5, z + 0.1))}
                                                className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-r-md">
                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24"
                                                 stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                      d="M12 4v16m8-8H4"/>
                                            </svg>
                                        </button>
                                    </div>
                                    <div ref={gridContainerRef}
                                         className="flex-1 overflow-auto p-4 flex bg-gray-50/50 relative">
                                        <div className="m-auto">
                                            <div className="grid gap-1 relative" style={{
                                                gridTemplateColumns: `repeat(${dimensions.width}, ${80 * zoom}px)`,
                                                gridTemplateRows: `repeat(${dimensions.height}, ${80 * zoom}px)`
                                            }}>
                                                {layoutTiles.map((tile) => {
                                                    const isHighlighted = hoveredType && tile.type === 'dispenser' && tile.dispensed_types.includes(hoveredType);
                                                    return (
                                                        <div
                                                            key={`${tile.x}-${tile.y}`}
                                                            className={`w-full h-full border flex flex-col items-center justify-center relative transition-colors
                                                                ${tile.type === 'empty' ? 'bg-white border-gray-300 text-gray-200' : ''}
                                                                ${tile.type === 'blocked' ? 'bg-gray-800 border-gray-900 text-white' : ''}
                                                                ${tile.type === 'interface' ? 'bg-blue-50 border-blue-300 text-blue-600 shadow-sm' : ''}
                                                                ${tile.type === 'mixer' ? 'bg-green-50 border-green-700 text-green-700 shadow-sm' : ''}
                                                                ${tile.type === 'capper' ? 'bg-red-50 border-red-700 text-red-700 shadow-sm' : ''}
                                                                ${tile.type === 'dispenser' ? (isHighlighted ? 'bg-green-100 border-green-500 text-green-700 shadow-md ring-2 ring-green-300' : 'bg-orange-50 border-orange-300 text-orange-600 shadow-sm') : ''}
                                                            `}
                                                            title={tile.type === 'dispenser' ? tile.dispensed_types.join('\n') : ''}
                                                        >
                                                            {tile.type === 'empty' &&
                                                                <PlusCircleIcon className="w-[45%] h-[45%]"/>}
                                                            {tile.type === 'blocked' &&
                                                                <XCircleIcon className="w-[45%] h-[45%]"/>}
                                                            {tile.type === 'interface' &&
                                                                <TruckIcon className="w-[45%] h-[45%]"/>}
                                                            {tile.type === 'mixer' &&
                                                                <ArrowPathIcon className="w-[45%] h-[45%]"/>}
                                                            {tile.type === 'capper' &&
                                                                <CircleStackIcon className="w-[45%] h-[45%]"/>}
                                                            {tile.type === 'dispenser' && (
                                                                <>
                                                                    {(tile.dispensed_types?.length > 0) && (
                                                                        <div
                                                                            className="absolute left-0 right-0 z-10 flex justify-center pointer-events-none"
                                                                            style={{
                                                                                top: `${4 * zoom}px`,
                                                                                padding: `0 ${4 * zoom}px`
                                                                            }}
                                                                        >
                                                                            <span
                                                                                className="font-bold text-orange-800 bg-white/90 border border-orange-200 rounded shadow-sm truncate leading-none"
                                                                                style={{
                                                                                    fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                                    padding: `${zoom}px ${4 * zoom}px`,
                                                                                    borderWidth: `${Math.max(1, zoom)}px`
                                                                                }}
                                                                            >
                                                                                {getDispenserInitials(tile.dispensed_types)}
                                                                            </span>
                                                                        </div>
                                                                    )}

                                                                    <FunnelIcon className="w-[45%] h-[45%] z-0"/>

                                                                    <div
                                                                        className="absolute left-1/2 -translate-x-1/2 z-10 flex items-center justify-center pointer-events-none"
                                                                        style={{bottom: `${4 * zoom}px`}}
                                                                    >
                                                                        <span
                                                                            className="font-bold text-orange-900 bg-orange-100 border border-orange-300 text-center rounded shadow-sm leading-none tracking-tighter"
                                                                            style={{
                                                                                fontSize: `${Math.max(5, 10 * zoom)}px`,
                                                                                padding: `${zoom}px`,
                                                                                minWidth: `${16 * zoom}px`,
                                                                                borderWidth: `${Math.max(1, zoom)}px`
                                                                            }}
                                                                        >
                                                                            {tile.dispensed_types?.length > 99 ? '99+' : (tile.dispensed_types?.length || 0)}
                                                                    </span>
                                                                    </div>
                                                                </>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <IngredientListInfoModal listId={infoIngredientListId}
                                                         onClose={() => setInfoIngredientListId(null)}/>
                            </div>

                            {/* Order List Tab */}
                            <div className={activeTab === 'order_list' ? 'p-6 overflow-y-auto flex-1' : 'hidden'}>
                                <div className="max-w-4xl mx-auto space-y-6 pb-8">
                                    <div
                                        className="bg-white p-4 rounded-md border border-gray-200 shadow-sm grid grid-cols-1 gap-3">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center">
                                            {data?.order_list.name ||
                                                <span className="text-gray-400 italic">No name provided</span>}
                                        </div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center capitalize">
                                            {data?.order_list.type ||
                                                <span className="text-gray-400 italic">No type provided</span>}
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        {data.order_list.orders?.map((order, orderIndex) => (
                                            <div key={orderIndex}
                                                 className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Order {orderIndex + 1}</h3>
                                                {data.order_list.type === 'perfume' && (
                                                    <div className="mb-4 sm:w-1/3">
                                                        <label className="block text-xs font-medium text-gray-500 mb-1">T
                                                            Max</label>
                                                        <div
                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{order.t_max ??
                                                            <span className="text-gray-400 italic">Not set</span>}</div>
                                                    </div>
                                                )}
                                                <div className="space-y-3">
                                                    {order.items.map((item, itemIndex) => {
                                                        const isMixer = item.name.toLowerCase() === 'mixer';
                                                        const isCapper = item.name.toLowerCase() === 'capper';
                                                        const isSpecial = isMixer || isCapper;

                                                        return (
                                                            <div key={itemIndex}
                                                                 className={`flex ${isSpecial ? 'items-center' : 'items-start'} gap-3`}>
                                                                <div className="flex-1">
                                                                    {!isSpecial && <label
                                                                        className="block text-xs font-medium text-gray-500 mb-1">Item
                                                                        Name</label>}
                                                                    {isSpecial ? (
                                                                        <div
                                                                            className={`w-full px-3 py-2 border rounded-md bg-gray-50 text-sm flex items-center gap-2 font-semibold min-h-9.5 ${isMixer ? 'text-green-700 border-green-200' : 'text-red-700 border-red-200'}`}>
                                                                            {isMixer ?
                                                                                <ArrowPathIcon className="w-4 h-4"/> :
                                                                                <CircleStackIcon className="w-4 h-4"/>}
                                                                            {isMixer ? 'Mixer' : 'Capper'}
                                                                        </div>
                                                                    ) : (
                                                                        <div
                                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                                            {item.name}
                                                                        </div>
                                                                    )}
                                                                </div>

                                                                {!isSpecial && (
                                                                    <div className="w-32">
                                                                        <label
                                                                            className="block text-xs font-medium text-gray-500 mb-1">Amount</label>
                                                                        <div
                                                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                                            {item.quantity}
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        ))}
                                        {(!data.order_list.orders || data.order_list.orders.length === 0) &&
                                            <p className="text-gray-500 text-center py-4">No orders found in this
                                                list.</p>}
                                    </div>
                                </div>
                            </div>
                            {/* Simulation Tab */}
                            <div className={activeTab === 'simulation' ? 'flex-1 min-h-0 bg-white relative' : 'hidden'}>
                                {data.status === 'finished' ? (
                                    <iframe
                                        src={`${SIMULATOR_URL}/${experimentId}/simulator?hide_gantt=true`}
                                        className="w-full h-full border-none"
                                        title="Simulation View"
                                    />
                                ) : (
                                    <div
                                        className="h-full flex flex-col items-center justify-center text-gray-500 space-y-3">
                                        <div className="text-center">
                                            <p className="text-lg font-semibold text-gray-900">Simulation is not
                                                available</p>
                                            <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                                Simulations are available only for finished experiments.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Gantt Chart Tab */}
                            <div className={activeTab === 'gantt' ? 'flex-1 min-h-0 bg-white flex flex-col relative' : 'hidden'}>
                                {data.status === 'finished' ? (
                                    isSimLoading ? (
                                        <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-2">
                                            <ArrowPathIcon className="w-6 h-6 animate-spin text-gray-700" />
                                            <span className="text-sm">Loading Gantt charts...</span>
                                        </div>
                                    ) : ganttNames.length > 0 ? (
                                        <div className="flex-1 flex flex-col min-h-0">
                                            {/* Chart Selector Bar */}
                                            <div className="px-6 py-2.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between shrink-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-1">
                                                        Chart:
                                                    </span>
                                                    <div className="inline-flex rounded-lg bg-gray-200/80 p-0.5 shadow-xs">
                                                        {ganttNames.map((name, idx) => (
                                                            <button
                                                                key={name}
                                                                onClick={() => setSelectedGanttIndex(idx)}
                                                                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                                                                    (selectedGanttIndex === idx || (!ganttNames[selectedGanttIndex] && idx === 0))
                                                                        ? 'bg-white text-gray-900 shadow-xs font-semibold'
                                                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/50'
                                                                }`}
                                                            >
                                                                {formatGanttName(name)}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                                {simulationData?.gantts?.max_path && (
                                                    <div className="text-xs text-gray-500 font-medium">
                                                        Total Duration: <span className="font-semibold text-gray-800">{simulationData.gantts.max_path} timesteps</span>
                                                    </div>
                                                )}
                                            </div>
                                            {/* Full-width, full-height plot iframe */}
                                            <div className="flex-1 min-h-0 w-full relative bg-white">
                                                <iframe
                                                    key={currentGanttUrl}
                                                    src={currentGanttUrl}
                                                    className="w-full h-full border-none"
                                                    title="Gantt Chart View"
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-3">
                                            <div className="text-center">
                                                <p className="text-lg font-semibold text-gray-900">No Gantt charts found</p>
                                                <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                                    No Gantt chart plots were generated for this simulation.
                                                </p>
                                            </div>
                                        </div>
                                    )
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-3">
                                        <div className="text-center">
                                            <p className="text-lg font-semibold text-gray-900">Gantt chart is not available</p>
                                            <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                                Gantt charts are available only for finished experiments.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>


                        </>
                    )}
                </div>

                {/* Footer */}
                {activeTab !== 'simulation' && activeTab !== 'gantt' && (
                    <div className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end shrink-0">
                        {data && onCopyCreate && (
                            <button
                                onClick={() => {
                                    handleClose();
                                    onCopyCreate(data);
                                }}
                                className="px-4 py-2 text-sm font-medium text-white bg-gray-900 border border-transparent rounded-md hover:bg-black shadow-sm flex items-center gap-2"
                            >
                                <DocumentDuplicateIcon className="w-4 h-4"/>
                                Copy & Create
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}