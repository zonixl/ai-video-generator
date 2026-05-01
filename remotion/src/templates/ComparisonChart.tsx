import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {clampPercent, parseParts} from './templateUtils';

export const ComparisonChart: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'success');
  const [beforeLabel = '之前', beforeRaw = '34', afterLabel = '之后', afterRaw = '89'] = parseParts(component, '之前|34|之后|89');
  const before = interpolate(frame, [0, fps], [0, clampPercent(Number.parseFloat(beforeRaw) || 0)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const after = interpolate(frame, [fps * 0.2, fps * 1.2], [0, clampPercent(Number.parseFloat(afterRaw) || 0)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const bar = (label: string, value: number, accent: string) => (
    <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12}}>
      <div style={{height: 135, width: 74, display: 'flex', alignItems: 'end'}}>
        <div style={{width: '100%', height: `${value}%`, borderRadius: 18, background: accent}} />
      </div>
      <div style={{fontSize: 36, fontWeight: 950, color: accent}}>{Math.round(value)}%</div>
      <div style={{fontSize: 23, fontWeight: 850, color: theme.mutedInk}}>{label}</div>
    </div>
  );

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '30px 34px',
        display: 'flex',
        gap: 22,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {bar(beforeLabel, before, '#94a3b8')}
      <div style={{width: 1, background: 'rgba(100,116,139,0.18)'}} />
      {bar(afterLabel, after, colors.accent)}
    </div>
  );
};
