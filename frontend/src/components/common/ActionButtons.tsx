import {InformationCircleIcon, PencilSquareIcon, TrashIcon} from '@heroicons/react/24/outline';

interface ActionButtonsProps {
    onInfo: () => void;
    onEdit?: () => void;
    onDelete: () => void;
    deleteDisabled?: boolean;
}

export default function ActionButtons({onInfo, onEdit, onDelete, deleteDisabled}: ActionButtonsProps) {
    return (
        <div className="flex space-x-2">
            <button onClick={onInfo}
                    className="text-green-800 hover:text-green-700 bg-green-50 p-1 rounded border border-green-700 shadow hover:shadow-md transition-all"
                    title="Info">
                <InformationCircleIcon className="w-5 h-5"/>
            </button>

            {onEdit && (
                <button onClick={onEdit}
                        className="text-gray-800 hover:text-gray-700 bg-gray-50 p-1 rounded border border-gray-700 shadow hover:shadow-md transition-all"
                        title="Edit">
                    <PencilSquareIcon className="w-5 h-5"/>
                </button>
            )}

            <button onClick={onDelete} disabled={deleteDisabled}
                    className="text-red-600 hover:text-red-500 bg-red-50 p-1 rounded border border-red-600 shadow hover:shadow-md transition-all disabled:opacity-50"
                    title="Delete">
                <TrashIcon className="w-5 h-5"/>
            </button>
        </div>
    );
}