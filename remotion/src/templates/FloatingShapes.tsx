import React from 'react';
import {useCurrentFrame} from 'remotion';

const SHAPES = [
  {x: 0.06, y: 0.10, size: 56, speed: 0.008, delay: 0, type: 'circle'},
  {x: 0.88, y: 0.14, size: 42, speed: 0.006, delay: 20, type: 'circle'},
  {x: 0.10, y: 0.74, size: 64, speed: 0.005, delay: 40, type: 'triangle'},
  {x: 0.78, y: 0.62, size: 48, speed: 0.009, delay: 10, type: 'circle'},
  {x: 0.44, y: 0.84, size: 38, speed: 0.007, delay: 30, type: 'circle'},
  {x: 0.66, y: 0.32, size: 50, speed: 0.008, delay: 50, type: 'triangle'},
  {x: 0.30, y: 0.38, size: 34, speed: 0.011, delay: 15, type: 'circle'},
  {x: 0.56, y: 0.18, size: 44, speed: 0.006, delay: 35, type: 'circle'},
  {x: 0.22, y: 0.56, size: 52, speed: 0.009, delay: 25, type: 'triangle'},
  {x: 0.92, y: 0.48, size: 30, speed: 0.012, delay: 5, type: 'circle'},
];

export const FloatingShapes: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden'}}>
      {SHAPES.map((shape, i) => {
        const driftX = Math.sin((frame + shape.delay) * shape.speed) * 40;
        const driftY = Math.cos((frame + shape.delay) * shape.speed * 1.3) * 32;
        const opacity = 0.05 + Math.sin((frame + shape.delay) / 60) * 0.025;

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
                borderBottom: `${shape.size}px solid rgba(14,165,233,${opacity * 18})`,
                transform: `translate(${driftX}px, ${driftY}px) rotate(${frame * 0.2}deg)`,
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
              background: `radial-gradient(circle, rgba(245,158,11,${opacity * 25}) 0%, transparent 70%)`,
              transform: `translate(${driftX}px, ${driftY}px)`,
            }}
          />
        );
      })}
    </div>
  );
};
