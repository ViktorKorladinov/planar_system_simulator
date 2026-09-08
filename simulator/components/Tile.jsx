import React, {memo, useEffect, useRef, useState} from 'react';
import {getColorFromGradient} from '@/utils/colorUtilities';

const Tile = memo(function NonMemoTile({
  w,
  h = w,
  x,
  y,
  idx,
  selected,
  maxPath,
  setMedicine,
  name = 'unavailable',
  speed,
}) {
  let color = getColorFromGradient(idx, maxPath);
  let tileType = 'tile';
  if (selected === 1) {
    color = 'lightgreen';
    tileType += 'selected';
  } else if (name === 'interface') {
    tileType += ' interface';
    color = 'lightblue';
  } else if (name === 'unavailable') {
    tileType += ' unavailable';
    color = 'lightgrey';
  }
  const [stateY, setStateY] = useState(y);
  const [stateX, setStateX] = useState(x);
  const trans = `fill ${speed}ms linear`;
  const textRef = useRef(null);

  useEffect(() => {
    setStateX(x + 10);
    setStateY(y + 60);
  }, [x, y]);
  return (<g className={tileType} onMouseEnter={() => {
    setMedicine(name);
  }} onMouseLeave={() => {
    setMedicine('');
  }}>
    <rect y={y} x={x} width={w} height={h} fill={color}
          style={{
            transition: trans,
            msTransition: trans,
            WebkitTransition: trans,
          }}/>
    <text ref={textRef} y={stateY} x={stateX} width={w} height={h}
          fontFamily="Verdana" fontSize="50"
          fill="black">{idx}</text>
  </g>);
});

export default Tile;