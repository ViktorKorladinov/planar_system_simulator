'use client';
import { useCallback, useEffect, useState } from 'react';
import '@/styles/portal.css';
import SimulationCard from '@/components/SimulationCard';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [parsedSimulations, setParsedSimulations] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const size = 20;
  const [hasNewSimulation, setHasNewSimulation] = useState(false);

  const fetchSimulations = useCallback(async (targetPage) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/simulations/?page=${targetPage}&size=${size}`);
      if (!response.ok) throw new Error('Failed to fetch simulations');

      const data = await response.json();
      setParsedSimulations(data.items);
      setTotalPages(data.total);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }, [size]);

  useEffect(() => {
    fetchSimulations(page);
  }, [page, fetchSimulations]);

  useEffect(() => {
    const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/notifications/stream`);

    eventSource.onmessage = (event) => {
      if (event.data === "experiment_finished") {
        setHasNewSimulation(true);
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const handleRefreshList = () => {
    setHasNewSimulation(false);
    if (page === 1) {
      fetchSimulations(1);
    } else {
      setPage(1);
    }
  };

  const renderSimulations = useCallback(() => {
    if (!parsedSimulations || parsedSimulations.length === 0) {
      return <h2 className="text-gray-500 mt-10">No simulations to be shown</h2>;
    }
    return parsedSimulations.map((sim, id) => (
        <SimulationCard simulationDetail={sim} key={`simCard${sim.id}`} id={id} />
    ));
  }, [parsedSimulations]);

  return (
      <>
        <div onClick={() => router.push('/')} className="hover:cursor-pointer absolute left-4 w-28 h-28">
          <Image id="aa" fill={true} alt="CIIRC Logo" src="/ciirc.svg" />
        </div>

        {hasNewSimulation && (
            <div className="fixed top-5 left-1/2 transform -translate-x-1/2 z-50 bg-blue-600 text-white px-6 py-3 rounded-full shadow-lg flex items-center gap-4 animate-bounce">
              <span>New simulations are ready!</span>
              <button
                  onClick={handleRefreshList}
                  className="bg-white text-blue-600 px-3 py-1 rounded-full text-sm font-bold hover:bg-gray-100 transition-colors"
              >
                Refresh List
              </button>
            </div>
        )}

        <div className="flex flex-col items-center justify-center mb-10 pt-10">
          <h1 className="p-4 text-3xl font-semibold text-gray-800">Available Simulations</h1>

          <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-5 justify-items-center p-5 w-[90%]">
            {renderSimulations()}
          </div>

          <div className="flex gap-2 mt-8 items-center bg-gray-100 p-2 rounded-lg shadow-sm">
            <button
                disabled={page <= 1}
                onClick={() => setPage(1)}
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-50"
            >
              &laquo; Newest
            </button>

            <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 hover:bg-blue-600"
            >
              Previous
            </button>

            <span className="px-4 font-medium text-gray-700">
            Page {page} of {totalPages}
          </span>

            <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 hover:bg-blue-600"
            >
              Next
            </button>

            <button
                disabled={page >= totalPages}
                onClick={() => setPage(totalPages)}
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded disabled:opacity-50 hover:bg-gray-50"
            >
              Oldest &raquo;
            </button>
          </div>
        </div>
      </>
  );
}