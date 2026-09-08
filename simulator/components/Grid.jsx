// noinspection JSValidateTypes,JSIncompatibleTypesComparison

'use client';
import {useState, useEffect, useRef, useCallback} from 'react';
import {animated, useSprings} from '@react-spring/web';
import Tile from './Tile';
import Toolbar from './Toolbar';
import {useMemo} from 'react';

const CELL_SIZE = 240;
const MOVER_SIZE = 112;
// m x n
export default function Grid({m, n, simulationData, fill}) {
  const medicineInfo = simulationData?.tile_type_dict || {};
  const dispenserInfo = simulationData?.dispenser_dict || {};
  const patientColors = simulationData?.order_color_dict || {};
  const ganttData = simulationData?.gantts || {};
  let simulationDatumElement = simulationData?.mover_paths?.paths || [];
  const positions = useMemo(() => {
    const logicalToExactPos = (allPaths) => {
      let resultPaths = allPaths.map(moverPath => {
        return moverPath.map(pos => {
          let newPos = {...pos};
          newPos.logicalX = pos.x;
          newPos.logicalY = pos.y;
          newPos.x = pos.x * CELL_SIZE + CELL_SIZE / 2 - MOVER_SIZE / 2;
          newPos.y = pos.y * CELL_SIZE + CELL_SIZE / 2 - MOVER_SIZE / 2;
          if (pos.mode === 'wait_rest') {
            newPos.x += pos['rest_offset_x'] * CELL_SIZE / 2;
            newPos.y += pos['rest_offset_y'] * CELL_SIZE / 2;
          }
          return newPos;
        });
      });

      if (resultPaths.length > 0) {
        const numTimeSteps = resultPaths[0].length;
        for (let t = 0; t < numTimeSteps; t++) {
          const tileGroups = {};
          for (let m = 0; m < resultPaths.length; m++) {
            const pos = resultPaths[m][t];
            if (pos.mode !== 'wait_rest') {
              const key = `${pos.logicalX},${pos.logicalY}`;
              if (!tileGroups[key]) tileGroups[key] = [];
              tileGroups[key].push(m);
            }
          }

          for (const key in tileGroups) {
            const moversOnTile = tileGroups[key];
            if (moversOnTile.length > 1) {
              const offset = CELL_SIZE / 4; // 60
              
              let groupIsHorizontal = false;
              let anyMoving = false;
              
              for (const moverIdx of moversOnTile) {
                 const pos = resultPaths[moverIdx][t];
                 const isEntering = t > 0 && (resultPaths[moverIdx][t-1].logicalX !== pos.logicalX || resultPaths[moverIdx][t-1].logicalY !== pos.logicalY);
                 const isLeaving = t < numTimeSteps - 1 && (resultPaths[moverIdx][t+1].logicalX !== pos.logicalX || resultPaths[moverIdx][t+1].logicalY !== pos.logicalY);
                 
                 if (isEntering || isLeaving) {
                    let dxLog = 0, dyLog = 0;
                    if (isEntering) {
                       dxLog = pos.logicalX - resultPaths[moverIdx][t-1].logicalX;
                       dyLog = pos.logicalY - resultPaths[moverIdx][t-1].logicalY;
                    } else {
                       dxLog = resultPaths[moverIdx][t+1].logicalX - pos.logicalX;
                       dyLog = resultPaths[moverIdx][t+1].logicalY - pos.logicalY;
                    }
                    groupIsHorizontal = Math.abs(dxLog) > Math.abs(dyLog);
                    anyMoving = true;
                    break; 
                 }
              }
              
              if (!anyMoving) {
                 const moverIdx = moversOnTile[0];
                 const pos = resultPaths[moverIdx][t];
                 let dxLog = 0, dyLog = 0;
                 let prevStep = t - 1;
                 while (prevStep >= 0) {
                    const prev = resultPaths[moverIdx][prevStep];
                    if (prev.logicalX !== pos.logicalX || prev.logicalY !== pos.logicalY) {
                       dxLog = pos.logicalX - prev.logicalX;
                       dyLog = pos.logicalY - prev.logicalY;
                       break;
                    }
                    prevStep--;
                 }
                 if (dxLog === 0 && dyLog === 0) {
                    let nextStep = t + 1;
                    while (nextStep < numTimeSteps) {
                       const next = resultPaths[moverIdx][nextStep];
                       if (next.logicalX !== pos.logicalX || next.logicalY !== pos.logicalY) {
                          dxLog = next.logicalX - pos.logicalX;
                          dyLog = next.logicalY - pos.logicalY;
                          break;
                       }
                       nextStep++;
                    }
                 }
                 groupIsHorizontal = Math.abs(dxLog) > Math.abs(dyLog);
              }
              
              moversOnTile.forEach((moverIdx, i) => {
                const pos = resultPaths[moverIdx][t];
                const sign = (i % 2 === 0) ? -1 : 1;
                
                if (groupIsHorizontal) {
                  pos.y += sign * offset;
                } else {
                  pos.x += sign * offset;
                }
              });
            }
          }
        }
      }
      return resultPaths;
    };

    return logicalToExactPos(simulationDatumElement);
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
  const progressRef = useRef(1);
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
    if (positions && positions.length > 0 && progressRef.current !==
        positions[0].length - 1) {
      let newCoords = [];
      for (const path of positions) {
        const nextStep = path[progressRef.current + 1];
        newCoords.push(nextStep);
      }
      api.start(index => {
        const position = newCoords[index];
        const pos = moversRefs.current[index];
        const currentLogical = positions[index][progressRef.current];
        
        let toArray = [];
        const dx = Math.abs(position.x - pos.x);
        const dy = Math.abs(position.y - pos.y);
        const totalDist = dx + dy;
        
        if (dx > 0 && dy > 0) {
          const durationX = animateRef.current * (dx / totalDist);
          const durationY = animateRef.current * (dy / totalDist);
          
          const nextLogical = position;
          const targetCenterY = nextLogical.logicalY * CELL_SIZE + CELL_SIZE / 2 - MOVER_SIZE / 2;
          const targetCenterX = nextLogical.logicalX * CELL_SIZE + CELL_SIZE / 2 - MOVER_SIZE / 2;
          
          const isTargetOffsetY = Math.abs(position.y - targetCenterY) > 1;
          const isTargetOffsetX = Math.abs(position.x - targetCenterX) > 1;
          
          let moveYFirst = false;
          if (dx > dy) {
            moveYFirst = isTargetOffsetY;
          } else {
            moveYFirst = !isTargetOffsetX;
          }
          
          if (moveYFirst) {
            toArray = [
              {y: position.y, config: {duration: durationY}}, 
              {x: position.x, config: {duration: durationX}}
            ];
          } else {
            toArray = [
              {x: position.x, config: {duration: durationX}}, 
              {y: position.y, config: {duration: durationY}}
            ];
          }
        } else if (dx > 0) {
          toArray = [{x: position.x, config: {duration: animateRef.current}}];
        } else if (dy > 0) {
          toArray = [{y: position.y, config: {duration: animateRef.current}}];
        } else {
          toArray = [{x: position.x, y: position.y, config: {duration: animateRef.current}}];
        }

        moversRefs.current[index] = {
          x: position.x,
          y: position.y,
        };
        return {
          from: {x: pos.x, y: pos.y},
          to: toArray
        };
      });
      progressRef.current += 1;
      setCounter(ct => ct + 1);
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
  }, [api, matrix, n, positions]);

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
    if (progressRef.current !==
        positions[0].length) requestRef.current = requestAnimationFrame(
        animateV); else progressRef.current -= 1;
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
        return (
            <animated.rect key={`mover${id}`} x={spring['x']} y={spring['y']}
                           width={MOVER_SIZE} height={MOVER_SIZE} style={{
              fill: `url(#bgPattern${id})`,
            }} rx="15">{id}</animated.rect>);
      })}
    </svg>
    <Toolbar counter={counter} length={positions[0]?.length || 0} animate={speed}
             medicineName={medicineName}
             consumeMove={consumeMove} setAnimate={setSpeed}
             setMedicine={setMedicine} ganttData={ganttData}/>
  </>);

}