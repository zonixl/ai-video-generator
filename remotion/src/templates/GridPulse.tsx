import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

export const GridPulse: React.FC<{style?: React.CSSProperties}> = ({style}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(Math.sin(frame / 18), [-1, 1], [0.08, 0.22]);

  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', ...style}}>
      {Array.from({length: 9}).map((_, index) => {
        const size = 180 + index * 42;
        const pulse = interpolate((frame + index * 6) % 90, [0, 90], [0.4, 1.5]);
        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: '50%',
              top: '36%',
              width: size,
              height: size,
              marginLeft: -size / 2,
              marginTop: -size / 2,
              borderRadius: '50%',
              border: '1px solid rgba(14,165,233,0.14)',
              transform: `scale(${pulse})`,
              opacity
            }}
          />
        );
      })}
    </div>
  );
};
