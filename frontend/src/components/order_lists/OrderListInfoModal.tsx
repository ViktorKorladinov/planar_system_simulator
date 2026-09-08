import {useQuery} from '@tanstack/react-query';
import {getOrderList} from '../../api/order_lists';
import type {OrderListSingleGetResponseDTO} from '../../types/order_lists';
import {ArrowPathIcon, CircleStackIcon, DocumentDuplicateIcon} from "@heroicons/react/24/outline";

interface OrderListInfoModalProps {
    orderListId: number | null;
    onClose: () => void;
    onCopyCreate?: (data: OrderListSingleGetResponseDTO) => void;
}

export default function OrderListInfoModal({orderListId, onClose, onCopyCreate}: OrderListInfoModalProps) {
    const {data, isLoading, isError} = useQuery({
        queryKey: ['order_list', orderListId],
        queryFn: () => getOrderList(orderListId!),
        enabled: !!orderListId,
    });

    if (!orderListId) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" onClick={onClose}></div>

            <div
                className="relative bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-2xl flex flex-col max-h-[90vh]">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center shrink-0">
                    <h2 className="text-xl font-bold text-gray-900">Order List Details</h2>
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
                            <div
                                className="bg-white p-4 rounded-md border border-gray-200 shadow-sm grid grid-cols-1 gap-3">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <div
                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center">
                                    {data?.name || <span className="text-gray-400 italic">No name provided</span>}
                                </div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                <div
                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-800 min-h-10.5 flex items-center capitalize">
                                    {data?.type || <span className="text-gray-400 italic">No type provided</span>}
                                </div>
                            </div>

                            <div className="space-y-6">
                                {data?.orders?.map((order, orderIndex) => (
                                    <div key={orderIndex}
                                         className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">
                                            Order {orderIndex + 1}
                                        </h3>

                                        {data?.type === 'perfume' && (
                                            <div className="mb-4 sm:w-1/3">
                                                <label className="block text-xs font-medium text-gray-500 mb-1">T
                                                    Max</label>
                                                <div
                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                    {order.t_max ??
                                                        <span className="text-gray-400 italic">Not set</span>}
                                                </div>
                                            </div>
                                        )}

                                        <div className="space-y-3">
                                            {order.items.map((item, itemIndex) => {
                                                const isMixer = item.name.toLowerCase() === 'mixer';
                                                const isCapper = item.name.toLowerCase() === 'capper';
                                                const isSpecial = isMixer || isCapper;

                                                return (
                                                    <div key={itemIndex}
                                                         className={`flex ${isSpecial ? 'items-center' : 'items-start'} gap-3`}>
                                                        <div className="flex-1">
                                                            {!isSpecial && <label
                                                                className="block text-xs font-medium text-gray-500 mb-1">Item
                                                                Name</label>}
                                                            {isSpecial ? (
                                                                <div
                                                                    className={`w-full px-3 py-2 border rounded-md bg-gray-50 text-sm flex items-center gap-2 font-semibold min-h-9.5 ${isMixer ? 'text-green-700 border-green-700' : 'text-red-700 border-red-700'}`}>
                                                                    {isMixer ? <ArrowPathIcon className="w-4 h-4"/> :
                                                                        <CircleStackIcon className="w-4 h-4"/>}
                                                                    {isMixer ? 'Mixer' : 'Capper'}
                                                                </div>
                                                            ) : (
                                                                <div
                                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                                    {item.name}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {!isSpecial && (
                                                            <div className="w-32">
                                                                <label
                                                                    className="block text-xs font-medium text-gray-500 mb-1">Amount</label>
                                                                <div
                                                                    className="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-800 min-h-9.5 flex items-center">
                                                                    {item.quantity}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}

                                {(!data?.orders || data.orders.length === 0) && (
                                    <p className="text-gray-500 text-center py-4">No orders found in this list.</p>
                                )}
                            </div>
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