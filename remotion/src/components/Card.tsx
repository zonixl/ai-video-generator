import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

export const Card: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant);
  return (
    <div
      style={{
        minHeight: 92,
        borderRadius: 18,
        border: `4px solid ${colors.border}`,
        background: colors.background,
        color: colors.color,
        boxShadow: `10px 10px 0 ${theme.shadow}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '18px 28px',
        fontSize: 36,
        fontWeight: 800,
        textAlign: 'center',
        lineHeight: 1.18,
        ...style
      }}
    >
      {component.text}
    </div>
  );
};
