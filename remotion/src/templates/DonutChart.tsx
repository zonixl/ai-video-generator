import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {clampPercent, parseParts} from './templateUtils';

export const DonutChart: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'warning');
  const [rawValue = '68', label = '完成度'] = parseParts(component, '68|完成度');
  const value = clampPercent(Number.parseFloat(rawValue) || 0);
  const progress = interpolate(frame, [0, fps * 1.1], [0, value], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const radius = 70;
  const circumference = 2 * Math.PI * radius;

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        boxShadow: theme.shadow,
        padding: 28,
        display: 'flex',
        alignItems: 'center',
        gap: 22,
        color: colors.color,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <svg width={170} height={170} viewBox="0 0 170 170">
        <circle cx={85} cy={85} r={radius} fill="none" stroke="rgba(100,116,139,0.14)" strokeWidth={18} />
        <circle
          cx={85}
          cy={85}
          r={radius}
          fill="none"
          stroke={colors.accent}
          strokeWidth={18}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress / 100)}
          transform="rotate(-90 85 85)"
        />
        <text x={85} y={95} textAnchor="middle" fontSize={34} fontWeight={950} fill={colors.color}>{Math.round(progress)}%</text>
      </svg>
      <div style={{fontSize: 30, fontWeight: 900, letterSpacing: '-0.05em', lineHeight: 1.18}}>{label}</div>
    </div>
  );
};
