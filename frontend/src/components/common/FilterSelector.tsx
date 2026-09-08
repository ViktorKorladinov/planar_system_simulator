import {useEffect, useRef, useState} from 'react';
import {AdjustmentsHorizontalIcon} from '@heroicons/react/24/outline';

export interface FilterOption {
    label: string;
    value: string;
}

export interface FilterCategory {
    id: string;
    label: string;
    options: FilterOption[];
}

interface FilterDropdownProps {
    categories: FilterCategory[];
    selectedValues: Record<string, string[]>;
    onChange: (newValues: Record<string, string[]>) => void;
}

export default function FilterSelector({categories, selectedValues, onChange}: FilterDropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const filterRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleCheckboxChange = (categoryId: string, optionValue: string, isChecked: boolean) => {
        const currentCategorySelections = selectedValues[categoryId] || [];
        let newCategorySelections;

        if (isChecked) {
            newCategorySelections = [...currentCategorySelections, optionValue];
        } else {
            newCategorySelections = currentCategorySelections.filter(v => v !== optionValue);
        }

        onChange({
            ...selectedValues,
            [categoryId]: newCategorySelections
        });
    };

    return (
        <div className="relative" ref={filterRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`text-gray-800 hover:text-gray-700 p-1 rounded border border-gray-700 shadow transition-all hover:shadow-md ${isOpen ? 'bg-gray-200' : 'bg-gray-50 hover:bg-gray-100'}`}
                title="Filter"
            >
                <AdjustmentsHorizontalIcon className="w-7 h-7"/>
            </button>

            {isOpen && (
                <div
                    className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-md shadow-lg z-20 p-5 min-w-max">
                    <div className="flex space-x-8">
                        {categories.map((category) => (
                            <div key={category.id} className="flex flex-col">
                                <h3 className="text-base font-bold text-gray-900 mb-3">{category.label}</h3>
                                <div className="space-y-2">
                                    {category.options.map((opt) => {
                                        const isChecked = selectedValues[category.id]?.includes(opt.value) ?? false;

                                        return (
                                            <label key={opt.value}
                                                   className="flex items-center space-x-3 cursor-pointer group">
                                                <input
                                                    type="checkbox"
                                                    checked={isChecked}
                                                    onChange={(e) => handleCheckboxChange(category.id, opt.value, e.target.checked)}
                                                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                                                />
                                                <span className="text-sm text-gray-700 group-hover:text-gray-900">
                                                    {opt.label}
                                                </span>
                                            </label>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}