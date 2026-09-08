interface PaginationProps {
    page: number;
    totalPages: number;
    onPageChange: (newPage: number) => void;
    isDisabled?: boolean;
}

export default function Pagination({page, totalPages, onPageChange, isDisabled}: PaginationProps) {
    return (
        <div
            className="bg-gray-50 px-6 py-3 border border-t-0 border-gray-200 rounded-b-lg flex items-center justify-between shrink-0">
            <span className="text-sm text-gray-700">
                Page <span className="font-medium">{page}</span> of <span className="font-medium">{totalPages}</span>
            </span>
            <div className="space-x-2">
                <button
                    onClick={() => onPageChange(Math.max(1, page - 1))}
                    disabled={page === 1 || isDisabled}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                    Previous
                </button>
                <button
                    onClick={() => onPageChange(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages || totalPages === 0 || isDisabled}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                    Next
                </button>
            </div>
        </div>
    );
}