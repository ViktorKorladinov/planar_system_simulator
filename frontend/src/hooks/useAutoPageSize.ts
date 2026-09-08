import { useState, useEffect, type RefObject } from 'react';

export function useAutoPageSize(
    containerRef: RefObject<HTMLDivElement | null>,
    rowHeight = 61,
    headerHeight = 50,
    safetyBuffer = 25
) {
    const [pageSize, setPageSize] = useState(10);

    useEffect(() => {
        const calculatePageSize = () => {
            if (!containerRef.current) return;
            const availableHeight = containerRef.current.clientHeight - headerHeight - safetyBuffer;
            const calculatedSize = Math.max(5, Math.floor(availableHeight / rowHeight));

            setPageSize((prevSize) => prevSize !== calculatedSize ? calculatedSize : prevSize);
        };

        const observer = new ResizeObserver(calculatePageSize);
        if (containerRef.current) observer.observe(containerRef.current);

        return () => observer.disconnect();
    }, [containerRef, rowHeight, headerHeight, safetyBuffer]);

    return { pageSize, setPageSize };
}