import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const MetricCard: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant ?? 'primary');
  const [value, label] = (component.text ?? '').split('|');
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
        ...style
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
          color: colors.accent
        }}
      >
        <Icon name={component.icon ?? 'target'} size={34} />
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
        <div style={{fontSize: 44, fontWeight: 950, letterSpacing: '-0.06em', lineHeight: 1}}>{value}</div>
        {label ? <div style={{fontSize: 24, fontWeight: 800, color: theme.mutedInk}}>{label}</div> : null}
      </div>
    </div>
  );
};
