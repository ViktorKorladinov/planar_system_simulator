import {type ChangeEvent, forwardRef, type SyntheticEvent, useImperativeHandle, useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {createConfiguration} from '../../../api/configurations';
import type {ConfigurationSingleCreateRequestDTO} from '../../../types/configurations';
import type {EntityState} from '../ExperimentCreateModal';
import ConfigurationSelectModal from '../../configurations/ConfigurationSelectModal';

interface Props {
    state: EntityState<ConfigurationSingleCreateRequestDTO>;
    setState: (updater: (prev: EntityState<ConfigurationSingleCreateRequestDTO>) => EntityState<ConfigurationSingleCreateRequestDTO>) => void;
}

export interface ConfigTabRef {
    discard: () => void;
    validate: () => Promise<ConfigurationSingleCreateRequestDTO | null>;
}

const INITIAL_FORM_STATE: ConfigurationSingleCreateRequestDTO = {
    name: '', solver_type: 'hexaly', interface_time: 3, dispensing_time: 1, mover_amount: 1,
    time_limit: 60, process_amount: 1, batch_size: 100, warmup: false, dispense_rate: 1,
    viscosity_exponent: 1, mover_speed: 1, mixer_primary_time: 1, mixer_final_time: 1, capper_time: 1,
};

const ExperimentConfigurationTab = forwardRef<ConfigTabRef, Props>(({state, setState}, ref) => {
    const [validationErrors, setValidationErrors] = useState<string[]>([]);
    const [isSelectModalOpen, setIsSelectModalOpen] = useState(false);

    const validateMutation = useMutation({
        mutationFn: async (data: ConfigurationSingleCreateRequestDTO) => {
            setValidationErrors([]);
            await createConfiguration(data, true);
            return data;
        },
        onSuccess: (sanitizedData) => {
            setState(prev => ({...prev, data: sanitizedData, isValidated: true, isValidating: false}));
        },
        onError: (errors: unknown) => {
            setState(prev => ({...prev, isValidated: false, isValidating: false}));
            if (Array.isArray(errors)) setValidationErrors(errors);
            else setValidationErrors(["Validation failed."]);
        }
    });

    const performValidation = async () => {
        if (!state.data) return null;
        setState(prev => ({...prev, isValidating: true}));
        const payload = {...state.data};

        if (typeof payload.name === 'string') {
            const trimmedName = payload.name.trim();
            payload.name = trimmedName.length > 0 ? trimmedName : (null as unknown as string);
        }

        if (payload.solver_type === 'hexaly') {
            payload.batch_size = null as unknown as number;
            payload.warmup = null as unknown as boolean;
            payload.dispense_rate = null as unknown as number;
            payload.viscosity_exponent = null as unknown as number;
            payload.mover_speed = null as unknown as number;
            payload.mixer_primary_time = null as unknown as number;
            payload.mixer_final_time = null as unknown as number;
            payload.capper_time = null as unknown as number;
        } else if (payload.solver_type === 'cplex_medicine') {
            payload.dispense_rate = null as unknown as number;
            payload.viscosity_exponent = null as unknown as number;
            payload.mover_speed = null as unknown as number;
            payload.mixer_primary_time = null as unknown as number;
            payload.mixer_final_time = null as unknown as number;
            payload.capper_time = null as unknown as number;
        } else if (payload.solver_type === 'cplex_perfumes') {
            payload.batch_size = null as unknown as number;
            payload.warmup = null as unknown as boolean;
        }

        try {
            return await validateMutation.mutateAsync(payload);
        } catch {
            return null;
        }
    };

    useImperativeHandle(ref, () => ({
        discard: () => {
            setState(() => ({mode: 'empty', id: null, data: null, isValidated: false, isValidating: false}));
            setValidationErrors([]);
        },
        validate: async () => {
            if (state.isValidated && state.data) return state.data as ConfigurationSingleCreateRequestDTO;
            return await performValidation();
        }
    }));

    const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const {name, value, type} = e.target;
        const checked = (e.target as HTMLInputElement).checked;

        setState(prev => {
            const prevData = prev.data || INITIAL_FORM_STATE;
            const newData = {
                ...prevData,
                [name]: type === 'checkbox' ? checked : type === 'number' ? (value === '' ? '' : Number(value)) : value
            };

            if (name === 'solver_type') {
                if (value === 'cplex_medicine') {
                    if (newData.batch_size == null) newData.batch_size = 100;
                    if (newData.warmup == null) newData.warmup = false;
                } else if (value === 'cplex_perfumes') {
                    if (newData.dispense_rate == null) newData.dispense_rate = 1;
                    if (newData.viscosity_exponent == null) newData.viscosity_exponent = 1;
                    if (newData.mover_speed == null) newData.mover_speed = 1;
                    if (newData.mixer_primary_time == null) newData.mixer_primary_time = 1;
                    if (newData.mixer_final_time == null) newData.mixer_final_time = 1;
                    if (newData.capper_time == null) newData.capper_time = 1;
                }
            }

            return {...prev, mode: 'draft', data: newData, isValidated: false, isValidating: false};
        });
    };

    const handleValidate = async (e: SyntheticEvent) => {
        e.preventDefault();
        await performValidation();
    };

    if (state.mode === 'empty') {
        return (
            <div className="h-full flex items-center justify-center gap-6">
                <button onClick={() => setIsSelectModalOpen(true)}
                        className="px-8 py-4 bg-white border border-gray-300 text-gray-700 rounded-lg shadow-sm hover:bg-gray-50 font-medium text-lg transition-colors">Select
                    Existing
                </button>
                <button onClick={() => setState(() => ({
                    mode: 'draft',
                    id: null,
                    data: INITIAL_FORM_STATE,
                    isValidated: false,
                    isValidating: false
                }))}
                        className="px-8 py-4 bg-gray-900 border border-gray-900 text-white rounded-lg shadow-sm hover:bg-black font-medium text-lg transition-colors">Create
                    New
                </button>
                <ConfigurationSelectModal
                    isOpen={isSelectModalOpen}
                    onClose={() => setIsSelectModalOpen(false)}
                    onSelect={(id, data) => {
                        setState(() => ({
                            mode: 'existing',
                            id,
                            data: data as unknown as ConfigurationSingleCreateRequestDTO,
                            isValidated: true,
                            isValidating: false
                        }));
                        setIsSelectModalOpen(false);
                    }}
                />
            </div>
        );
    }

    const formData = state.data || INITIAL_FORM_STATE;
    const isMedicine = formData.solver_type === 'cplex_medicine';
    const isPerfume = formData.solver_type === 'cplex_perfumes';

    return (
        <div className="h-full relative overflow-y-auto p-6">
            {state.mode === 'existing' && (
                <div
                    className="max-w-4xl mx-auto mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800 text-center shadow-sm">
                    Using existing Configuration. Modifying fields will detach it and create a new draft.
                </div>
            )}
            <form id="config-tab-form" onSubmit={handleValidate} className="space-y-6 max-w-4xl mx-auto pb-8">
                {validationErrors.length > 0 && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-md relative shrink-0 shadow-sm">
                        <button type="button" onClick={() => setValidationErrors([])}
                                className="absolute top-2 right-2 text-red-400 hover:text-red-600">✕
                        </button>
                        <h4 className="text-sm font-semibold text-red-800 mb-1">Validation Errors:</h4>
                        <ul className="text-sm text-red-700 list-disc pl-5">
                            {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}

                <div className="bg-white p-5 rounded-md border border-gray-200 shadow-sm space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                        <input type="text" name="name" value={formData.name || ''} onChange={handleChange}
                               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 text-sm"
                               placeholder="Configuration name... (Optional)"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Solver Type</label>
                        <select name="solver_type" value={formData.solver_type} onChange={handleChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-gray-500 bg-white text-sm">
                            <option value="hexaly">Hexaly</option>
                            <option value="cplex_medicine">Cplex Medicine</option>
                            <option value="cplex_perfumes">Cplex Perfumes</option>
                        </select>
                    </div>
                </div>

                <div className="bg-white p-5 rounded-md border border-gray-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b border-gray-100 pb-2">General
                        Parameters</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div><label className="block text-xs font-medium text-gray-500 mb-1">Interface Time
                            (s)</label><input required type="number" min="1" name="interface_time"
                                              value={formData.interface_time ?? ''} onChange={handleChange}
                                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                        </div>
                        <div><label className="block text-xs font-medium text-gray-500 mb-1">Dispensing Time (s)</label><input
                            required type="number" min="1" name="dispensing_time" value={formData.dispensing_time ?? ''}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/></div>
                        <div><label className="block text-xs font-medium text-gray-500 mb-1">Mover Amount</label><input
                            required type="number" min="1" name="mover_amount" value={formData.mover_amount ?? ''}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/></div>
                        <div><label className="block text-xs font-medium text-gray-500 mb-1">Time Limit
                            (s)</label><input required type="number" min="1" name="time_limit"
                                              value={formData.time_limit ?? ''} onChange={handleChange}
                                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                        </div>
                        <div className="col-span-2"><label className="block text-xs font-medium text-gray-500 mb-1">Process
                            Amount</label><input required type="number" min="1" name="process_amount"
                                                 value={formData.process_amount ?? ''} onChange={handleChange}
                                                 className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                        </div>
                    </div>
                </div>

                {isMedicine && (
                    <div className="bg-white p-5 rounded-md border border-gray-200 shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b border-gray-100 pb-2">Additional
                            Parameters</h3>
                        <div className="space-y-4">
                            <div className="w-1/2 pr-2"><label className="block text-xs font-medium text-gray-500 mb-1">Batch
                                Size</label><input required={isMedicine} type="number" min="1" name="batch_size"
                                                   value={formData.batch_size ?? ''} onChange={handleChange}
                                                   className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                            </div>
                            <div className="flex items-center"><input type="checkbox" name="warmup"
                                                                      checked={!!formData.warmup}
                                                                      onChange={handleChange}
                                                                      className="h-4 w-4 text-gray-600 rounded"/><label
                                className="ml-2 block text-sm font-medium text-gray-900">Enable Warmup</label></div>
                        </div>
                    </div>
                )}

                {isPerfume && (
                    <div className="bg-white p-5 rounded-md border border-gray-200 shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b border-gray-100 pb-2">Additional
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
                                                       value={formData.viscosity_exponent ?? ''} onChange={handleChange}
                                                       className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                            </div>
                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Mover Speed (s per
                                tile)</label><input required={isPerfume} type="number" step="any" min="0.001"
                                                    name="mover_speed" value={formData.mover_speed ?? ''}
                                                    onChange={handleChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                            </div>
                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer Primary Time
                                (s)</label><input required={isPerfume} type="number" step="1" min="1"
                                                  name="mixer_primary_time" value={formData.mixer_primary_time ?? ''}
                                                  onChange={handleChange}
                                                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                            </div>
                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Mixer Final Time
                                (s)</label><input required={isPerfume} type="number" step="1" min="1"
                                                  name="mixer_final_time" value={formData.mixer_final_time ?? ''}
                                                  onChange={handleChange}
                                                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/>
                            </div>
                            <div><label className="block text-xs font-medium text-gray-500 mb-1">Capper Time (s)</label><input
                                required={isPerfume} type="number" step="1" min="1" name="capper_time"
                                value={formData.capper_time ?? ''} onChange={handleChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"/></div>
                        </div>
                    </div>
                )}
            </form>
        </div>
    );
});

export default ExperimentConfigurationTab;