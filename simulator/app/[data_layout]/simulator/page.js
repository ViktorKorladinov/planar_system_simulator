'use client'
import { useEffect, useState } from "react"
import '../../../styles/grid.css'
import Grid from "../../../components/Grid";
import Image from "next/image";
import { useParams, useRouter } from 'next/navigation';

export default function Simulator() {
    const router = useRouter();
    const [simulationData, setSimData] = useState();
    const [size, setSize] = useState({ n: 0, m: 0, fill: false });
    const params = useParams();
    const simulationId = params.data_layout; // This is the ID from the URL

    const apiUrl = (!process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_URL.includes('backend'))
        ? '/api/v1'
        : process.env.NEXT_PUBLIC_API_URL;

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${apiUrl}/simulations/${simulationId}`);
                if (!response.ok) throw new Error('Simulation not found');

                const jsonData = await response.json();
                setSimData(jsonData);

                let moverPaths = jsonData.mover_paths;
                setSize({ n: moverPaths.m, m: moverPaths.n, fill: moverPaths.filled });
            } catch (error) {
                console.error("Failed to load simulation:", error);
            }
        };
        void fetchData();
    }, [simulationId]);

    const [hideGantt, setHideGantt] = useState(false);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('hide_gantt') === 'true' || urlParams.get('no_gantt') === 'true') {
                setHideGantt(true);
            }
        }
    }, []);

    if (!simulationData) {
        return (
            <main>
                <p>Loading Files..</p>
            </main>
        )
    }

    const isEmbedded = typeof window !== 'undefined' && window.self !== window.top;

    return (
        <main>
            {!isEmbedded && (
                <div onClick={() => router.push('/')} className="hover:cursor-pointer absolute left-4 w-28 h-28">
                    <Image id="aa" fill={true} alt="CIIRC Logo" src={"/ciirc.svg"} />
                </div>
            )}
            <section className="gridHolder">
                <Grid
                    n={size.n}
                    m={size.m}
                    fill={size.fill}
                    simulationData={simulationData}
                    simulationId={simulationId}
                    hideGantt={hideGantt}
                />
            </section>
        </main>
    );
}