import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {clampPercent, parseChartItems} from './templateUtils';

export const LineChart: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'success');
  const items = parseChartItems(component.text, '一:30;二:48;三:62;四:78;五:92').slice(0, 6);
  const width = 380;
  const height = 180;
  const progress = interpolate(frame, [0, fps * 1.2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const points = items.map((item, index) => {
    const x = 24 + (index / Math.max(1, items.length - 1)) * (width - 48);
    const y = height - 28 - (clampPercent(item.value) / 100) * (height - 56);
    return {x, y, label: item.label};
  });
  const d = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: 26,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        <path d={d} fill="none" stroke={colors.accent} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
        {points.map((point, index) => (
          <circle key={point.label} cx={point.x} cy={point.y} r={progress > index / points.length ? 8 : 0} fill={colors.accent} />
        ))}
      </svg>
      <div style={{display: 'flex', justifyContent: 'space-between', color: theme.mutedInk, fontSize: 19, fontWeight: 800}}>
        {points.map((point) => <span key={point.label}>{point.label}</span>)}
      </div>
    </div>
  );
};
