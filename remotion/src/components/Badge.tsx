import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

export const Badge: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant ?? 'warning');
  return (
    <div
      style={{
        borderRadius: 16,
        border: `4px solid ${colors.border}`,
        background: colors.background,
        boxShadow: `8px 8px 0 ${theme.shadow}`,
        padding: '18px 28px',
        fontSize: 34,
        fontWeight: 900,
        textAlign: 'center',
        ...style
      }}
    >
      {component.text}
    </div>
  );
};
