import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const MetricCard: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({
  component,
  style,
}) => {
  const colors = variantStyle(component.variant ?? 'primary');
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [value, label] = (component.text ?? '').split('|');
  const numValue = Number.parseFloat(value?.replace(/[^\d.-]/g, '') ?? '') || 0;
  const isNumber = /^\d/.test(value?.trim() ?? '');

  // entrance + number scroll
  const enter = spring({frame: frame - 4, fps, config: {damping: 14, stiffness: 140, mass: 0.8}});
  const scroll = isNumber
    ? Math.round(interpolate(frame, [0, fps * 1.0], [0, numValue], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))
    : null;

  return (
    <div
      style={{
        minHeight: 128,
        borderRadius: 30,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        color: colors.color,
        boxShadow: theme.shadow,
        padding: '26px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        backdropFilter: 'blur(18px)',
        opacity: Math.min(1, enter),
        transform: `scale(${0.9 + enter * 0.1})`,
        ...style,
      }}
    >
      <div
        style={{
          width: 62,
          height: 62,
          borderRadius: 22,
          background: 'rgba(255,255,255,0.66)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.accent,
        }}
      >
        <Icon name={component.icon ?? 'target'} size={34} />
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
        <div style={{fontSize: 44, fontWeight: 950, letterSpacing: '-0.06em', lineHeight: 1}}>
          {scroll !== null ? scroll : value}
        </div>
        {label ? <div style={{fontSize: 24, fontWeight: 800, color: theme.mutedInk}}>{label}</div> : null}
      </div>
    </div>
  );
};
