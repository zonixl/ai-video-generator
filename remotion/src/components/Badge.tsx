import React from 'react';
import type {ComponentSpec} from '../schema';
import {variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const Badge: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant ?? 'warning');
  return (
    <div
      style={{
        borderRadius: 999,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        color: colors.color,
        boxShadow: '0 14px 40px rgba(28,35,58,0.10)',
        padding: '16px 28px',
        fontSize: 30,
        fontWeight: 900,
        textAlign: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        letterSpacing: '-0.03em',
        backdropFilter: 'blur(14px)',
        ...style
      }}
    >
      <Icon name={component.icon} size={30} color={colors.accent} />
      <span>{component.text}</span>
    </div>
  );
};
