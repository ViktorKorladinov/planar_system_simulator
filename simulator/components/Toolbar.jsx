'use client'
import React, {useEffect, useRef, useState} from 'react';
import '../styles/toolbar.css'

function Toolbar({counter, length, animate, setAnimate, consumeMove, prevMove, goToFrame, medicineName, ganttData, moverCount}) {
    const [selectedGantt, setSelectedGantt] = useState(0)
    const [btnStates, setStates] = useState(["", "", "", "", ""])
    const [barMode, setBarMode] = useState('barAttached')
    const gridIframe = useRef(null);
    const [contentWindow, setContentWindow] = useState(null)
    const contentWindowRef = useRef();

    const [ganttHeightMode, setGanttHeightMode] = useState('auto'); // 'auto', 'compact', 'standard'
    const isEmbedded = typeof window !== 'undefined' && window.self !== window.top;

    const calculateHeight = React.useCallback(() => {
        const count = moverCount || 12;
        if (ganttHeightMode === 'compact') {
            return Math.min(160, Math.max(110, 20 + count * 10));
        }
        if (ganttHeightMode === 'standard') {
            return Math.max(240, 44 + count * 18);
        }
        // Auto mode
        if (isEmbedded) {
            // When embedded inside details page modal, use compact height to maximize tile grid room
            return Math.min(165, Math.max(115, 22 + count * 11));
        }
        if (typeof window !== 'undefined' && window.innerHeight < 860) {
            // Compact mode for 13" MacBook Air and smaller displays (viewport height < 860px)
            return Math.max(180, 34 + count * 16);
        }
        // Standard mode for large monitors
        return Math.max(240, 44 + count * 18);
    }, [moverCount, ganttHeightMode, isEmbedded]);

    const [iframeHeight, setIframeHeight] = useState(calculateHeight);

    useEffect(() => {
        const handleResize = () => {
            setIframeHeight(calculateHeight());
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [calculateHeight]);

    useEffect(() => {
        setIframeHeight(calculateHeight());
    }, [calculateHeight]);

    const ganttNamesArray = ganttData?.names || [];

    useEffect(() => {
        // noinspection JSValidateTypes
        contentWindowRef.current = contentWindow
    }, [contentWindow])

    const select = (idx, animation) => {
        const states = ["", "", "", "", ""]
        if (animation < 0) {
            if (animate !== 0) {
                setAnimate(0)
            }
            if (animation < -1) {
                consumeMove()
            }
        } else {
            states[idx] = "selected"
            setAnimate(animation)
        }
        setStates(states)
    }

    let iframeItem = gridIframe.current ? gridIframe.current.contentWindow : null

    useEffect(() => {
        if(iframeItem == null) return
       iframeItem.postMessage({
                type: 'UPDATE_MARKER',
                position: counter
            }, '*');
    }, [ animate, counter, iframeItem])

    const handleGrid = () => {
        const iframeItem = gridIframe.current.contentWindow
        iframeItem.postMessage({
            type: 'UPDATE_MARKER',
            position: counter
        }, '*');
        setContentWindow(iframeItem)
    }

    const showMedicine = () => {
        let splitMedicineName = medicineName.split(',').join(', ')
        if (medicineName.length !== 0)
            return <div className="text-xs medicine">{splitMedicineName}</div>
    }

    const plotBaseUrl = ganttData?.api_plot_url ? (
        (ganttData.api_plot_url.startsWith('http')
            ? new URL(ganttData.api_plot_url).pathname
            : ganttData.api_plot_url).replace(/\/$/, '')
    ) : '';

    return (<div className={barMode}>
        <div className="toolbarWrapper">
            {showMedicine()}
            <div className="toolbar">
                <div style={{ display: 'flex', alignItems: 'center', marginRight: '10px' }}>
                    <span style={{ fontWeight: 600, minWidth: '95px' }}>Frame: {counter}/{length}</span>
                    <input
                        type="range"
                        min="1"
                        max={Math.max(1, length)}
                        value={counter}
                        onChange={(e) => {
                            select(0, -1); // pause playback
                            if (goToFrame) {
                                goToFrame(Number(e.target.value) - 1, false);
                            }
                        }}
                        className="frameSlider"
                        title="Seek to frame"
                    />
                </div>
                <div className='flex gap-1'>
                    <button onClick={() => { select(0, -1); if (prevMove) prevMove(); }}>Prev</button>
                    <button className={btnStates[0]} onClick={() => select(0, -2)}>Next</button>
                    <button className={btnStates[1] + " separate"} onClick={() => select(1, 500)}>
                        <span>Play </span>
                    </button>
                    <button className={btnStates[2]} onClick={() => select(2, 250)}><span>Fast </span>
                    </button>
                    <button className={btnStates[3]} onClick={() => select(3, 50)}><span>Fastest </span>
                    </button>
                    <button onClick={() => select(0, -1)}><span>Pause</span></button>
                </div>
                <button
                    className="separate"
                    onClick={() => setBarMode(state => state === 'barAttached' ? 'barDetached' : 'barAttached')}
                    title={barMode === 'barAttached' ? 'Hide Gantt chart and float toolbar' : 'Show and attach Gantt chart'}
                >
                    <span>{barMode === 'barAttached' ? 'Detach' : 'Attach'}</span>
                </button>
                {barMode === 'barAttached' && (
                    <button
                        type="button"
                        onClick={() => setGanttHeightMode(mode => (mode === 'compact' || (mode === 'auto' && isEmbedded)) ? 'standard' : 'compact')}
                        title="Toggle compact or expanded Gantt height"
                    >
                        <span>{(ganttHeightMode === 'compact' || (ganttHeightMode === 'auto' && isEmbedded)) ? 'Expand Gantt' : 'Compact Gantt'}</span>
                    </button>
                )}

                <div className="chartButtons">
                    <button
                        onClick={() => setSelectedGantt(idx => ((idx > 0 ? idx - 1 : ganttNamesArray.length - 1)))}>
                        <span>Prev</span></button>
                    <button
                        onClick={() => setSelectedGantt(idx => ((idx + 1) % ganttNamesArray.length))}>
                        <span>Next</span></button>
                </div>
            </div>
        </div>
        <iframe ref={gridIframe} onLoad={handleGrid}
                scrolling="auto"
                style={{
                    height: `${iframeHeight}px`,
                    minHeight: `${iframeHeight}px`,
                    width: '100%',
                    border: 'none',
                    display: 'block',
                    overflowX: 'auto',
                    overflowY: 'hidden'
                }}
                src={ganttNamesArray.length > 0 && plotBaseUrl ? `${plotBaseUrl}/${ganttNamesArray[selectedGantt]}` : ""} title="Gantt"/>
    </div>);
}

export default Toolbar;