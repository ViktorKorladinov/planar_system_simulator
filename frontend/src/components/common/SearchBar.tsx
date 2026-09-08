import {MagnifyingGlassIcon} from '@heroicons/react/24/outline';
import type {KeyboardEvent} from 'react';

interface SearchBarProps {
    value: string;
    placeholder?: string;
    onChange: (value: string) => void;
    onSearch: () => void;
}

export default function SearchBar({value, placeholder = "Search...", onChange, onSearch}: SearchBarProps) {
    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') onSearch();
    };

    return (
        <div className="flex items-center space-x-2 flex-1 max-w-sm">
            <input
                type="text"
                placeholder={placeholder}
                className="w-full px-4 py-2 border border-gray-300 bg-gray-200 focus:bg-white rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 transition-colors"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={handleKeyDown}
            />
            <button
                onClick={onSearch}
                className="text-gray-800 hover:text-gray-700 bg-gray-50 p-1 rounded border border-gray-700 shadow transition-all hover:shadow-md hover:bg-gray-100"
                title="Search"
            >
                <MagnifyingGlassIcon className="w-7 h-7"/>
            </button>
        </div>
    );
}