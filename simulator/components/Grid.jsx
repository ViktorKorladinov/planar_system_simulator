// noinspection JSValidateTypes,JSIncompatibleTypesComparison

'use client';
import {useState, useEffect, useRef, useCallback} from 'react';
import {animated, useSprings} from '@react-spring/web';
import Tile from './Tile';
import Toolbar from './Toolbar';
import {useMemo} from 'react';

import {processMoverTrajectories, CELL_SIZE, MOVER_SIZE} from '../utils/trajectoryProcessor';

// m x n
export default function Grid({m, n, simulationData, fill}) {
  const medicineInfo = simulationData?.tile_type_dict || {};
  const dispenserInfo = simulationData?.dispenser_dict || {};
  const patientColors = simulationData?.order_color_dict || {};
  const ganttData = simulationData?.gantts || {};
  let simulationDatumElement = simulationData?.mover_paths?.paths || [];
  const positions = useMemo(() => {
    return processMoverTrajectories(simulationDatumElement);
  }, [simulationDatumElement]);

  const [counter, setCounter] = useState(1);
  const [speed, setSpeed] = useState(0);
  const [matrix, setMatrix] = useState(() => {
    return Array.from({length: m}, () => Array(n).fill(0));
  });
  const [selected, setSelected] = useState(() => {
    return Array.from({length: m}, () => Array(n).fill(0));
  });
  const [medicineName, setMedicine] = useState('');

  const statePosC = positions.map(
      arr => ({x: arr[0].x, y: arr[0].y}));
  const [srpingVals, api] = useSprings(positions.length, idx => ({
    from: statePosC[idx],
  }));

  const moversRefs = useRef(statePosC);
  const requestRef = useRef();
  const previousTimeRef = useRef();
  const animateRef = useRef(0);
  const progressRef = useRef(0);
  const medicineRef = useRef('');

  // react to animation speed change
  useEffect(() => {
    animateRef.current = speed;
  }, [speed]);

  // react to medicine selection
  useEffect(() => {
    if (medicineName === medicineRef.current) return;
    let updatedSelected = Array.from({length: m}, () => Array(n).fill(0));
    if (medicineName.length > 0) {
      for (const singleMedicineName of medicineName.split(',')) {
        if (singleMedicineName === 'unavailable') continue;
        for (let coordinate of medicineInfo[singleMedicineName]) {
          const x = coordinate[0];
          const y = coordinate[1];
          updatedSelected[x][y] = 1;
        }
      }
      medicineRef.current = medicineName;
    } else {
      medicineRef.current = '';
    }
    setSelected(updatedSelected);
  }, [medicineInfo, matrix, m, medicineName, n, selected]);

  const consumeMove = useCallback(() => {
    if (positions && positions.length > 0 && progressRef.current < positions[0].length - 1) {
      const nextStepIdx = progressRef.current + 1;
      let newCoords = [];
      for (const path of positions) {
        newCoords.push(path[nextStepIdx]);
      }
      api.start(index => {
        const position = newCoords[index];
        const pos = moversRefs.current[index];
        const prevStep = positions[index]?.[progressRef.current];
        const nextStep = position;

        moversRefs.current[index] = {
          x: position.x,
          y: position.y,
        };

        return {
          from: {x: pos.x, y: pos.y},
          to: {x: position.x, y: position.y},
          config: {duration: animateRef.current},
          immediate: animateRef.current === 0,
        };
      });
      progressRef.current = nextStepIdx;
      setCounter(nextStepIdx + 1);
      const updatedMatrix = [...matrix]; // Update heatmap
      for (const pos of newCoords) {
        const {logicalX, logicalY, mode} = pos;
        if (mode !== 'transit') {
          continue;
        }
        updatedMatrix[logicalX][logicalY] += 1;
      }
      setMatrix(updatedMatrix);
    }
  }, [api, matrix, positions]);

  const animateV = useCallback(time => {
    if (previousTimeRef.current !== undefined) {
      const deltaTime = time - previousTimeRef.current;
      if (animateRef.current > 0 && deltaTime >= animateRef.current) {
        consumeMove();
        previousTimeRef.current = time - (deltaTime % animateRef.current);
      }
    } else {
      previousTimeRef.current = time;
    }
    if (positions && positions.length > 0 && progressRef.current < positions[0].length - 1) {
      requestRef.current = requestAnimationFrame(animateV);
    }
  }, [consumeMove, positions]);

  useEffect(() => {
    window.abc = (val) => {
      const name = val['points'][0]['data']['offsetgroup'];
      if (name in medicineInfo) {
        setMedicine(name);
      }
    };
    window.reset = () => {
      setMedicine('');
    };
    window.legend = (data) => {
      setMedicine(medicine => {
        const newMed = data['data'][data['curveNumber']]['legendgroup'];
        if (medicine === newMed) {
          return '';
        } else {
          return newMed;
        }
      });
    };
    requestRef.current = requestAnimationFrame(animateV);
    return () => cancelAnimationFrame(requestRef.current);
  }, [animateV, medicineInfo]);

  const placeTiles = () => {
    let res = [];
    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        if (fill || i === 0 || j === 0 || i === m - 1 || j === n - 1) {
          res.push(<Tile maxPath={ganttData['max_path']}
                         setMedicine={setMedicine} selected={selected[i][j]}
                         speed={speed} key={`${i}x${j}`}
                         name={dispenserInfo[`${i}x${j}`]}
                         w={CELL_SIZE} x={i * CELL_SIZE} y={j * CELL_SIZE}
                         idx={matrix[i][j]}/>);
        }
      }
    }
    return res;
  };

  return (<>
    <svg viewBox={`-5 -5 ${m * CELL_SIZE + 10} ${n * CELL_SIZE + 10}`}
         xmlns="http://www.w3.org/2000/svg">
      <defs>
        {srpingVals.map((spring, id) => (
            <pattern key={`def${id}`} id={`bgPattern${id}`}
                     patternUnits="userSpaceOnUse" width="20"
                     height="20">

              <rect width="20" height="20"
                    fill={patientColors[positions[id][progressRef.current]['order']]}/>
              <path d="M-1,1 l2,-2
                        M0,20 l20,-20
                        M19,21 l2,-2"
                    stroke="black" strokeWidth="4"/>
            </pattern>))}
      </defs>

      <g id="gridSvg">
        {placeTiles()}
      </g>
      {srpingVals.map((spring, id) => {
        const currentStep = positions[id]?.[progressRef.current];
        const isMulti = currentStep && currentStep.stackCount > 1;
        const isTopMover = currentStep && currentStep.stackIdx === currentStep.stackCount - 1;

        return (
          <g key={`moverGroup${id}`}>
            <animated.rect
              key={`mover${id}`}
              x={spring['x']}
              y={spring['y']}
              width={MOVER_SIZE}
              height={MOVER_SIZE}
              style={{
                fill: `url(#bgPattern${id})`,
                filter: isMulti
                  ? 'drop-shadow(0px 4px 8px rgba(0,0,0,0.5))'
                  : 'drop-shadow(0px 2px 4px rgba(0,0,0,0.25))',
                stroke: isMulti ? '#fbbf24' : '#ffffff',
                strokeWidth: isMulti ? '3' : '2',
                opacity: 0.94,
              }}
              rx="15"
            />
            {/* Multi-mover badge: displayed on top mover when 2+ movers share a tile */}
            {isMulti && isTopMover && (
              <g pointerEvents="none">
                <animated.circle
                  cx={spring.x.to(x => x + MOVER_SIZE - 12)}
                  cy={spring.y.to(y => y + 12)}
                  r="14"
                  fill="#ef4444"
                  stroke="#ffffff"
                  strokeWidth="2.5"
                />
                <animated.text
                  x={spring.x.to(x => x + MOVER_SIZE - 12)}
                  y={spring.y.to(y => y + 16.5)}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="12"
                  fontWeight="bold"
                  fontFamily="sans-serif"
                >
                  {`×${currentStep.stackCount}`}
                </animated.text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
    <Toolbar counter={counter} length={positions[0]?.length || 0} animate={speed}
             medicineName={medicineName}
             consumeMove={consumeMove} setAnimate={setSpeed}
             setMedicine={setMedicine} ganttData={ganttData}/>
  </>);

}