interface SortableHeaderProps {
    label: string;
    field: string;
    currentSortBy: string;
    currentSortDir: 'asc' | 'desc';
    onSort: (field: string) => void;
}

export default function SortableHeader({label, field, currentSortBy, currentSortDir, onSort}: SortableHeaderProps) {
    const isActive = currentSortBy === field;

    return (
        <th
            className="px-6 py-3 text-left text-sm font-medium text-black-500 tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={() => onSort(field)}
        >
            <div className="flex items-center space-x-1">
                <span>{label}</span>
                <div className="flex flex-col text-[8px] leading-none">
                    <span className={isActive && currentSortDir === 'asc' ? 'text-gray-900' : 'text-gray-300'}>▲</span>
                    <span className={isActive && currentSortDir === 'desc' ? 'text-gray-900' : 'text-gray-300'}>▼</span>
                </div>
            </div>
        </th>
    );
}