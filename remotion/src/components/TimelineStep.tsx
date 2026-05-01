import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const TimelineStep: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant ?? 'default');
  return (
    <div
      style={{
        minHeight: 118,
        borderRadius: 28,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.72)',
        boxShadow: '0 18px 44px rgba(28,35,58,0.11)',
        display: 'grid',
        gridTemplateColumns: '58px 1fr',
        alignItems: 'center',
        gap: 18,
        padding: '22px 26px',
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <div
        style={{
          width: 58,
          height: 58,
          borderRadius: 20,
          background: colors.background,
          color: colors.accent,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Icon name={component.icon ?? 'check'} size={32} />
      </div>
      <div
        style={{
          fontSize: 30,
          fontWeight: 850,
          color: theme.ink,
          lineHeight: 1.18,
          letterSpacing: '-0.04em'
        }}
      >
        {component.text}
      </div>
    </div>
  );
};
