'use client'
import React, {useEffect, useRef, useState} from 'react';
import '../styles/toolbar.css'

function Toolbar({counter, length, animate, setAnimate, consumeMove, prevMove, goToFrame, medicineName, ganttData}) {
    const [selectedGantt, setSelectedGantt] = useState(0)
    const [btnStates, setStates] = useState(["", "", "", "", ""])
    const [barMode, setBarMode] = useState('barAttached')
    const gridIframe = useRef(null);
    const [contentWindow, setContentWindow] = useState(null)
    const contentWindowRef = useRef();

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
                    onClick={() => setBarMode(state => state === 'barAttached' ? 'barDetached' : 'barAttached')}>
                    <span>{barMode === 'barAttached' ? 'Detach' : 'Attach'}</span>
                </button>

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
                src={ganttNamesArray.length > 0 ? `${ganttData?.api_plot_url}/${ganttNamesArray[selectedGantt]}` : ""} title="Gantt"/>
    </div>);
}

export default Toolbar;