import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {variantStyle} from '../styles/theme';

export const BackgroundPattern: React.FC<{component?: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component?.variant ?? 'primary');

  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden', ...style}}>
      {Array.from({length: 14}).map((_, index) => {
        const rotate = spring({frame: frame - index * 3, fps, from: 0, to: 1, config: {damping: 60}});
        const size = 220 + index * 38;
        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: '50%',
              top: '42%',
              width: size,
              height: size,
              marginLeft: -size / 2,
              marginTop: -size / 2,
              borderRadius: `${18 + index * 2}%`,
              border: `1px solid ${colors.border}`,
              transform: `rotate(${rotate * (28 + index * 3)}deg)`,
              opacity: 0.22
            }}
          />
        );
      })}
    </div>
  );
};
