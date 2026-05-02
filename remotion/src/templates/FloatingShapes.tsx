import React from 'react';
import {useCurrentFrame} from 'remotion';

const SHAPES = [
  {x: 0.08, y: 0.12, size: 48, speed: 0.012, delay: 0, type: 'circle'},
  {x: 0.82, y: 0.18, size: 36, speed: 0.009, delay: 20, type: 'circle'},
  {x: 0.14, y: 0.72, size: 56, speed: 0.007, delay: 40, type: 'triangle'},
  {x: 0.76, y: 0.68, size: 42, speed: 0.011, delay: 10, type: 'circle'},
  {x: 0.46, y: 0.82, size: 32, speed: 0.008, delay: 30, type: 'circle'},
  {x: 0.64, y: 0.38, size: 44, speed: 0.01, delay: 50, type: 'triangle'},
];

export const FloatingShapes: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden'}}>
      {SHAPES.map((shape, i) => {
        const driftX = Math.sin((frame + shape.delay) * shape.speed) * 30;
        const driftY = Math.cos((frame + shape.delay) * shape.speed * 1.3) * 24;
        const opacity = 0.04 + Math.sin((frame + shape.delay) / 72) * 0.02;

        if (shape.type === 'triangle') {
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `${shape.x * 100}%`,
                top: `${shape.y * 100}%`,
                width: 0,
                height: 0,
                borderLeft: `${shape.size * 0.5}px solid transparent`,
                borderRight: `${shape.size * 0.5}px solid transparent`,
                borderBottom: `${shape.size}px solid rgba(14,165,233,${opacity * 20})`,
                transform: `translate(${driftX}px, ${driftY}px) rotate(${frame * 0.3}deg)`,
              }}
            />
          );
        }
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${shape.x * 100}%`,
              top: `${shape.y * 100}%`,
              width: shape.size,
              height: shape.size,
              borderRadius: '50%',
              background: `radial-gradient(circle, rgba(245,158,11,${opacity * 30}) 0%, transparent 70%)`,
              transform: `translate(${driftX}px, ${driftY}px)`,
            }}
          />
        );
      })}
    </div>
  );
};
