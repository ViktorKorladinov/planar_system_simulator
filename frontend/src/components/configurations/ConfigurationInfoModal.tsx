import {useQuery} from '@tanstack/react-query';
import {getConfiguration} from '../../api/configurations';
import {formatSolverType} from "../../utils/formatters.ts";
import type {ConfigurationSingleGetResponseDTO} from '../../types/configurations';
import {DocumentDuplicateIcon} from '@heroicons/react/24/outline';

interface InfoModalProps {
    configId: number | null;
    onClose: () => void;
    onCopyCreate?: (data: ConfigurationSingleGetResponseDTO) => void;
}

export default function ConfigurationInfoModal({configId, onClose, onCopyCreate}: InfoModalProps) {
    const {data, isLoading, isError} = useQuery({
        queryKey: ['configuration', configId],
        queryFn: () => getConfiguration(configId!),
        enabled: !!configId,
    });

    if (!configId) return null;

    const isMedicine = data?.solver_type === 'cplex_medicine';
    const isPerfume = data?.solver_type === 'cplex_perfumes';

    return (
        <div className="fixed inset-0 z-80 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-[1px]" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Configuration Details</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>

                <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50">
                    {isLoading ? (
                        <p className="text-gray-500 text-center py-10">Loading details...</p>
                    ) : isError ? (
                        <p className="text-red-500 text-center py-10">Failed to load data.</p>
                    ) : (
                        <div className="space-y-6">
                            {/* Main Setup Info */}
                            <div
                                className="bg-white p-4 rounded-md border border-gray-200 shadow-sm grid grid-cols-1 gap-4">
                                <div className="col-span-2 sm:col-span-1">
                                    <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                                    <div
                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 text-sm min-h-9.5 flex items-center">
                                        {data?.name || <span className="text-gray-400 italic">Unnamed</span>}
                                    </div>
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-xs font-medium text-gray-500 mb-1">Solver Type</label>
                                    <div
                                        className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 text-sm min-h-9.5 flex items-center">
                                        {formatSolverType(data?.solver_type)}
                                    </div>
                                </div>
                            </div>

                            {/* General Parameters */}
                            <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">General
                                    Parameters</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Interface Time
                                            (s)</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.interface_time}</div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Dispensing Time
                                            (s)</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.dispensing_time}</div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Movers</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.mover_amount}</div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Time Limit
                                            (s)</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.time_limit}</div>
                                    </div>
                                    <div className="col-span-2">
                                        <label
                                            className="block text-xs font-medium text-gray-500 mb-1">Processes</label>
                                        <div
                                            className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.process_amount}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Medicine Constraints */}
                            {isMedicine && (
                                <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                        Parameters</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Batch
                                                Size</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.batch_size ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label
                                                className="block text-xs font-medium text-gray-500 mb-1">Warmup</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.warmup ? 'Yes' : 'No'}</div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Perfume Constraints */}
                            {isPerfume && (
                                <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                        Parameters</h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Dispense
                                                Rate (s/ml)</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.dispense_rate ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Viscosity
                                                Exponent</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.viscosity_exponent ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Mover Speed
                                                (s per tile)</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.mover_speed ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Mixer
                                                Primary Time (s)</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.mixer_primary_time ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Mixer Final
                                                Time (s)</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.mixer_final_time ?? '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 mb-1">Capper Time
                                                (s)</label>
                                            <div
                                                className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">{data?.capper_time ?? '-'}</div>
                                        </div>
                                    </div>
                                </div>
                            )}

                        </div>
                    )}
                </div>

                <div className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end shrink-0">
                    {data && onCopyCreate && (
                        <button
                            onClick={() => onCopyCreate(data)}
                            className="px-4 py-2 text-sm font-medium text-white bg-gray-900 border border-transparent rounded-md hover:bg-black shadow-sm flex items-center gap-2"
                        >
                            <DocumentDuplicateIcon className="w-4 h-4"/>
                            Copy & Create
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}