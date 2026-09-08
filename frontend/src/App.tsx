import {BrowserRouter, Navigate, Route, Routes} from 'react-router-dom';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import TopNav from './components/layout/TopNav';
import ExperimentsPage from './pages/ExperimentsPage';
import ConfigurationsPage from './pages/ConfigurationsPage';
import OrderListsPage from "./pages/OrderListsPage.tsx";
import LayoutsPage from "./pages/LayoutsPage.tsx";
import BatchesPage from "./pages/BatchesPage.tsx";
import IngredientListsPage from "./pages/IngredientListsPage.tsx";
import {useEffect} from "react";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            staleTime: 1000 * 60 * 5,
        },
    },
});

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1';

function App() {
    useEffect(() => {
        const eventSource = new EventSource(`${API_BASE_URL}/notifications/stream`);

        eventSource.onmessage = (event) => {
            if (event.data === 'experiment_running' || event.data === 'experiment_finished' || event.data === 'experiment_failed') {
                queryClient.invalidateQueries({queryKey: ['experiments']});
                queryClient.invalidateQueries({queryKey: ['batches']});
            }
        };

        eventSource.onerror = (error) => {
            console.error("SSE connection lost. Reconnecting...", error);
        };

        return () => {
            eventSource.close();
        };
    }, []);

    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <div className="h-screen overflow-hidden bg-gray-50 flex flex-col">
                    <TopNav/>
                    <main className="flex-1 flex flex-col min-h-0">
                        <Routes>
                            <Route path="/" element={<ExperimentsPage/>}/>
                            <Route path="/experiments" element={<ExperimentsPage/>}/>
                            <Route path="/configurations" element={<ConfigurationsPage/>}/>
                            <Route path="/layouts" element={<LayoutsPage/>}/>
                            <Route path="/ingredient-lists" element={<IngredientListsPage/>}/>
                            <Route path="/order-lists" element={<OrderListsPage/>}/>
                            <Route path="/batches" element={<BatchesPage/>}/>
                            <Route path="*" element={<Navigate to="/" replace/>}/>
                        </Routes>
                    </main>
                </div>
            </BrowserRouter>
        </QueryClientProvider>
    )
}

export default App;