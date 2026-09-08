export const formatSolverType = (type: string | undefined): string => {
    if (!type) return '-';

    const solverMap: Record<string, string> = {
        'hexaly': 'Hexaly Medicine',
        'cplex_medicine': 'Cplex Medicine',
        'cplex_perfumes': 'Cplex Perfumes'
    };

    return solverMap[type] || type;
};

export const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
};

export const formatWarmup = (warmup: boolean | null) => {
    if (warmup === null) return '-';
    return warmup ? 'Enabled' : 'Disabled';
};

export const formatName = (name?: string) => {
    if (!name) return '-';
    return name;
};

export const formatBatchSize = (batch_size: number | null) => {
    if (batch_size === null) return '-';
    return batch_size;
};

export const formatDispenseRate = (dispense_rate: number | null) => {
    if (dispense_rate === null) return '-';
    return dispense_rate;
};

export const formatMoverSpeed = (mover_speed: number | null) => {
    if (mover_speed === null) return '-';
    return mover_speed;
};

export const formatViscosityExponent = (viscosity_exponent: number | null) => {
    if (viscosity_exponent === null) return '-';
    return viscosity_exponent;
};

export const formatMixerPrimaryTime = (mixer_primary_time: number | null) => {
    if (mixer_primary_time === null) return '-';
    return mixer_primary_time;
};

export const formatMixerFinalTime = (mixer_final_time: number | null) => {
    if (mixer_final_time === null) return '-';
    return mixer_final_time;
};

export const formatCapperTime = (capper_time: number | null) => {
    if (capper_time === null) return '-';
    return capper_time;
};

export const formatLayoutType = (type: string | undefined): string => {
    if (!type) return '-';

    const typeMap: Record<string, string> = {
        'line': 'Line',
        'double_line': 'Double Line',
        'square': 'Square',
        'ring': 'Ring',
        'custom': 'Custom'
    };

    return typeMap[type] || type;
};

export const formatExperimentStatus = (type: string | undefined): string => {
    if (!type) return '-';

    const statusMap: Record<string, string> = {
        'queued': 'Queued',
        'running': 'Running',
        'finished': 'Finished',
        'failed': 'Failed'
    };

    return statusMap[type] || type;
};

export const formatOrderListType = (type: string | undefined): string => {
    if (!type) return '-';

    const typeMap: Record<string, string> = {
        'medicine': 'Medicine',
        'perfume': 'Perfume'
    };

    return typeMap[type] || type;
};

export const formatIngredientListType = (type: string | undefined): string => {
    if (!type) return '-';

    const typeMap: Record<string, string> = {
        'medicine': 'Medicine',
        'perfume': 'Perfume'
    };

    return typeMap[type] || type;
};