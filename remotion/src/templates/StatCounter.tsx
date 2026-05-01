import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from '../components/Icon';

export const StatCounter: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'primary');
  const [rawValue = '0', label = '关键指标', suffix = ''] = (component.text ?? '').split('|');
  const value = Number.parseFloat(rawValue.replace(/[^\d.-]/g, '')) || 0;
  const current = interpolate(frame, [0, fps * 1.2], [0, value], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        boxShadow: theme.shadow,
        padding: '30px 34px',
        display: 'flex',
        alignItems: 'center',
        gap: 22,
        color: colors.color,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <div
        style={{
          width: 68,
          height: 68,
          borderRadius: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255,255,255,0.66)',
          color: colors.accent
        }}
      >
        <Icon name={component.icon ?? 'zap'} size={38} />
      </div>
      <div>
        <div style={{fontSize: 58, fontWeight: 950, letterSpacing: '-0.07em', lineHeight: 1}}>
          {Math.round(current)}
          {suffix}
        </div>
        <div style={{fontSize: 25, fontWeight: 850, color: theme.mutedInk, marginTop: 8}}>{label}</div>
      </div>
    </div>
  );
};
