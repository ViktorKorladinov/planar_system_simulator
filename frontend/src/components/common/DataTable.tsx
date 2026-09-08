import type {ReactNode, RefObject} from 'react';

interface DataTableProps {
    containerRef: RefObject<HTMLDivElement | null>;
    headers: ReactNode;
    children: ReactNode;
}

export default function DataTable({containerRef, headers, children}: DataTableProps) {
    return (
        <div ref={containerRef}
             className="flex-1 min-h-0 overflow-auto bg-white border border-gray-200 rounded-t-lg shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 relative">
                <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
                <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-black-500 tracking-wider w-24">Actions</th>
                    {headers}
                </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                {children}
                </tbody>
            </table>
        </div>
    );
}