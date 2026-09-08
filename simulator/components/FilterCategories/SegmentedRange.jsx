import {useState, useEffect, useCallback} from 'react';

const SegmentedRange = ({min, max, intervals, onChange}) => {
    const [selectedSegments, setSelectedSegments] = useState(new Array(intervals).fill(true));

    const segmentSize = (max - min) / intervals;

    const getSegmentRange = useCallback((index) => {
        const start = min + (segmentSize * index);
        const end = start + segmentSize;
        return {
            start: Math.round(start * 100) / 100, end: Math.round(end * 100) / 100
        };
    }, [min, segmentSize]);

    const toggleSegment = (index) => {
        const newSelected = [...selectedSegments];
        newSelected[index] = !newSelected[index];
        setSelectedSegments(newSelected);
    };

    useEffect(() => {
        const selectedRanges = selectedSegments
            .map((isSelected, index) => isSelected ? getSegmentRange(index) : null)
            .filter(range => range !== null);
        onChange(selectedRanges);
    }, [getSegmentRange, onChange, selectedSegments]);

    return (<div className="w-full h-10">
        <div className="flex w-full h-full bg-gray-100 rounded-lg overflow-hidden">
            {selectedSegments.map((isSelected, index) => {

                let segmentClass = 'flex-1 flex items-center justify-center relative cursor-pointer transition-all duration-200 border-r border-gray-200 last:border-r-0 '
                if (isSelected) {
                    segmentClass += 'bg-blue-500 text-white hover:bg-blue-600'
                } else {
                    segmentClass += 'bg-white text-gray-700 hover:bg-blue-100'
                }

                return (<div key={index} onClick={() => toggleSegment(index)} className={segmentClass}>
                        <span className="text-sm whitespace-nowrap p-2">
                        {getSegmentRange(index).start} - {getSegmentRange(index).end}
                    </span>
                </div>);
            })}
        </div>
    </div>);
};

export default SegmentedRange;