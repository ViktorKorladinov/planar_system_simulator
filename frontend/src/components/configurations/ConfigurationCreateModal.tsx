import {type ChangeEvent, type SyntheticEvent, useState} from 'react';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import {createConfiguration} from '../../api/configurations';
import type {ConfigurationSingleCreateRequestDTO, ConfigurationSingleGetResponseDTO} from '../../types/configurations';
import {formatName} from "../../utils/formatters.ts";

interface CreateConfigurationModalProps {
    isOpen: boolean;
    initialData?: ConfigurationSingleGetResponseDTO | null;
    onClose: () => void;
    onSuccessSubmit: (name: string, id: number) => void;
}

const INITIAL_FORM_STATE: ConfigurationSingleCreateRequestDTO = {
    name: '',
    solver_type: 'hexaly',
    interface_time: 3,
    dispensing_time: 1,
    mover_amount: 1,
    time_limit: 60,
    process_amount: 1,
    batch_size: 100,
    warmup: false,
    dispense_rate: 1,
    viscosity_exponent: 1,
    mover_speed: 1,
    mixer_primary_time: 1,
    mixer_final_time: 1,
    capper_time: 1,
};

export default function ConfigurationCreateModal({
                                                     isOpen,
                                                     initialData,
                                                     onClose,
                                                     onSuccessSubmit
                                                 }: CreateConfigurationModalProps) {
    const queryClient = useQueryClient();
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    const [formData, setFormData] = useState<ConfigurationSingleCreateRequestDTO>(INITIAL_FORM_STATE);
    const [lastCopiedId, setLastCopiedId] = useState<number | null>(null);

    if (initialData && initialData.id !== lastCopiedId) {
        setLastCopiedId(initialData.id);
        setFormData({
            name: initialData.name ? `${initialData.name} (Copy)` : 'Copy',
            solver_type: initialData.solver_type,
            interface_time: initialData.interface_time,
            dispensing_time: initialData.dispensing_time,
            mover_amount: initialData.mover_amount,
            time_limit: initialData.time_limit,
            process_amount: initialData.process_amount,
            batch_size: initialData.batch_size ?? INITIAL_FORM_STATE.batch_size,
            warmup: initialData.warmup ?? INITIAL_FORM_STATE.warmup,
            dispense_rate: initialData.dispense_rate ?? INITIAL_FORM_STATE.dispense_rate,
            viscosity_exponent: initialData.viscosity_exponent ?? INITIAL_FORM_STATE.viscosity_exponent,
            mover_speed: initialData.mover_speed ?? INITIAL_FORM_STATE.mover_speed,
            mixer_primary_time: initialData.mixer_primary_time ?? INITIAL_FORM_STATE.mixer_primary_time,
            mixer_final_time: initialData.mixer_final_time ?? INITIAL_FORM_STATE.mixer_final_time,
            capper_time: initialData.capper_time ?? INITIAL_FORM_STATE.capper_time,
        });
    }

    const resetState = () => {
        setFormData(INITIAL_FORM_STATE);
        setValidationErrors([]);
        setLastCopiedId(null);
    };

    const mutation = useMutation({
        mutationFn: async (data: ConfigurationSingleCreateRequestDTO) => {
            setValidationErrors([]);
            await createConfiguration(data, true);
            return await createConfiguration(data, false);
        },
        onSuccess: async (createdData) => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['configurations']}),
                queryClient.invalidateQueries({queryKey: ['configuration']}),
                queryClient.invalidateQueries({queryKey: ['configurations_select']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']}),
                queryClient.invalidateQueries({queryKey: ['batches']})
            ]);

            onSuccessSubmit(formatName(createdData.name), createdData.id);
            resetState();
            onClose();
        },
        onError: (errors: unknown) => {
            if (Array.isArray(errors)) setValidationErrors(errors);
            else setValidationErrors(["An unexpected error occurred while saving."]);
        }
    });

    const handleDiscard = () => {
        if (window.confirm("Are you sure you want to discard your changes? This will reset the entire form.")) {
            resetState();
            onClose();
        }
    };

    const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const {name, value, type} = e.target;
        const checked = (e.target as HTMLInputElement).checked;

        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked :
                type === 'number' ? (value === '' ? '' : Number(value)) : value
        }));
    };

    const handleSubmit = (e: SyntheticEvent<HTMLFormElement>) => {
        e.preventDefault();

        const payload: ConfigurationSingleCreateRequestDTO = {...formData};

        if (typeof payload.name === 'string') {
            const trimmedName = payload.name.trim();
            payload.name = trimmedName.length > 0 ? trimmedName : null;
        }

        if (payload.solver_type === 'hexaly') {
            payload.batch_size = null;
            payload.warmup = null;
            payload.dispense_rate = null;
            payload.viscosity_exponent = null;
            payload.mover_speed = null;
            payload.mixer_primary_time = null;
            payload.mixer_final_time = null;
            payload.capper_time = null;
        } else if (payload.solver_type === 'cplex_medicine') {
            payload.dispense_rate = null;
            payload.viscosity_exponent = null;
            payload.mover_speed = null;
            payload.mixer_primary_time = null;
            payload.mixer_final_time = null;
            payload.capper_time = null;
        } else if (payload.solver_type === 'cplex_perfumes') {
            payload.batch_size = null;
            payload.warmup = null;
        }

        mutation.mutate(payload);
    };

    const isMedicine = formData.solver_type === 'cplex_medicine';
    const isPerfume = formData.solver_type === 'cplex_perfumes';

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" onClick={onClose}></div>
            <div
                className="relative bg-white rounded-lg shadow-2xl border border-gray-200 w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Create Configuration</h2>
                    <button onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                  d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                {validationErrors.length > 0 && (
                    <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md relative shrink-0">
                        <button onClick={() => setValidationErrors([])}
                                className="absolute top-2 right-2 text-red-400 hover:text-red-600">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                      d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                        <h4 className="text-sm font-semibold text-red-800 mb-1">Validation Errors:</h4>
                        <ul className="text-sm text-red-700 list-disc pl-5 max-h-24 overflow-y-auto">
                            {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}
                <form id="create-config-form" onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0"
                      autoComplete="off">
                    <div className="p-6 overflow-y-auto flex-1 bg-gray-50/50 space-y-6">
                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input type="text" name="name" value={formData.name || ''} onChange={handleChange}
                                       className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 text-sm"
                                       placeholder="Configuration name... (Optional)"/>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Solver Type</label>
                                <select name="solver_type" value={formData.solver_type} onChange={handleChange}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 focus:border-gray-500 bg-white text-sm">
                                    <option value="hexaly">Hexaly</option>
                                    <option value="cplex_medicine">Cplex Medicine</option>
                                    <option value="cplex_perfumes">Cplex Perfumes</option>
                                </select>
                            </div>
                        </div>

                        <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">General
                                Parameters</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Interface Time
                                    (s)</label><input required type="number" min="1" name="interface_time"
                                                      value={formData.interface_time ?? ''} onChange={handleChange}
                                                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                </div>
                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Dispensing Time
                                    (s)</label><input required type="number" min="1" name="dispensing_time"
                                                      value={formData.dispensing_time ?? ''} onChange={handleChange}
                                                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                </div>
                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Mover
                                    Amount</label><input required type="number" min="1" name="mover_amount"
                                                         value={formData.mover_amount ?? ''} onChange={handleChange}
                                                         className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                </div>
                                <div><label className="block text-xs font-medium text-gray-500 mb-1">Time Limit
                                    (s)</label><input required type="number" min="1" name="time_limit"
                                                      value={formData.time_limit ?? ''} onChange={handleChange}
                                                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                </div>
                                <div className="col-span-2"><label
                                    className="block text-xs font-medium text-gray-500 mb-1">Process
                                    Amount</label><input required type="number" min="1" name="process_amount"
                                                         value={formData.process_amount ?? ''} onChange={handleChange}
                                                         className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                </div>
                            </div>
                        </div>

                        {isMedicine && (
                            <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                    Parameters</h3>
                                <div className="space-y-4">
                                    <div className="w-1/2 pr-2"><label
                                        className="block text-xs font-medium text-gray-500 mb-1">Batch
                                        Size</label><input required={isMedicine} type="number" min="1" name="batch_size"
                                                           value={formData.batch_size ?? ''} onChange={handleChange}
                                                           className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div className="flex items-center"><input type="checkbox" name="warmup"
                                                                              checked={!!formData.warmup}
                                                                              onChange={handleChange}
                                                                              className="h-4 w-4 text-gray-600 rounded"/><label
                                        className="ml-2 block text-sm font-medium text-gray-900">Enable Warmup</label>
                                    </div>
                                </div>
                            </div>
                        )}

                        {isPerfume && (
                            <div className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Additional
                                    Parameters</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Dispense Rate
                                        (s/ml)</label><input required={isPerfume} type="number" step="any" min="0.001"
                                                             name="dispense_rate" value={formData.dispense_rate ?? ''}
                                                             onChange={handleChange}
                                                             className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Viscosity
                                        Exponent</label><input required={isPerfume} type="number" step="any" min="0.001"
                                                               name="viscosity_exponent"
                                                               value={formData.viscosity_exponent ?? ''}
                                                               onChange={handleChange}
                                                               className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Mover Speed (s
                                        per tile)</label><input required={isPerfume} type="number" step="any"
                                                                min="0.001" name="mover_speed"
                                                                value={formData.mover_speed ?? ''}
                                                                onChange={handleChange}
                                                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer Primary
                                        Time (s)</label><input required={isPerfume} type="number" step="1" min="1"
                                                               name="mixer_primary_time"
                                                               value={formData.mixer_primary_time ?? ''}
                                                               onChange={handleChange}
                                                               className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer Final
                                        Time (s)</label><input required={isPerfume} type="number" step="1" min="1"
                                                               name="mixer_final_time"
                                                               value={formData.mixer_final_time ?? ''}
                                                               onChange={handleChange}
                                                               className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                    <div><label className="block text-xs font-medium text-gray-500 mb-1">Capper Time
                                        (s)</label><input required={isPerfume} type="number" step="1" min="1"
                                                          name="capper_time" value={formData.capper_time ?? ''}
                                                          onChange={handleChange}
                                                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    <div
                        className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg flex justify-end space-x-3 shrink-0">
                        <button type="button" onClick={handleDiscard}
                                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 hover:border-red-300 transition-colors">Discard
                        </button>
                        <button type="submit" disabled={mutation.isPending}
                                className="px-4 py-2 text-sm font-medium text-white bg-gray-800 border border-transparent rounded-md hover:bg-gray-900 disabled:opacity-50 flex items-center">{mutation.isPending ? 'Validating...' : 'Create Configuration'}</button>
                    </div>
                </form>
            </div>
        </div>
    );
}