import {useMutation, useQueryClient} from "@tanstack/react-query";
import {useState} from "react";
import {updateOrderList} from "../../api/order_lists.ts";

interface UpdateModalProps {
    config: { id: number; name: string } | null;
    onClose: () => void;
    onSuccess: (msg: string, id: number) => void;
    onError: (msg: string) => void;
}

export default function OrderListUpdateModal({config, onClose, onSuccess, onError}: UpdateModalProps) {
    const queryClient = useQueryClient();
    const [name, setName] = useState(config?.name || '');

    const mutation = useMutation({
        mutationFn: () => updateOrderList(config!.id, {name}),
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({queryKey: ['order_lists']}),
                queryClient.invalidateQueries({queryKey: ['experiments']}),
                queryClient.invalidateQueries({queryKey: ['experiment_details']}),
                queryClient.invalidateQueries({queryKey: ['batches']})
            ]);
            onSuccess(`${name} updated successfully!`, config!.id);
            onClose();
        },
        onError: () => {
            onError(`Failed to update ${name}.`);
        }
    });

    if (!config) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/10 backdrop-blur-sm">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6" onClick={e => e.stopPropagation()}>
                <h2 className="text-xl font-bold mb-4">Update Order List</h2>

                <form onSubmit={(e) => {
                    e.preventDefault();
                    mutation.mutate();
                }}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                        <input required type="text" value={name} onChange={(e) => setName(e.target.value)}
                               className="w-full px-3 py-2 border rounded-md focus:ring-gray-500"/>
                    </div>

                    <div className="flex justify-end space-x-2">
                        <button type="button" onClick={onClose}
                                className="px-4 py-2 border rounded-md hover:bg-gray-50">Cancel
                        </button>
                        <button type="submit" disabled={mutation.isPending}
                                className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900">
                            {mutation.isPending ? 'Updating...' : 'Save'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}