import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const TextBlock: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant);
  const isTitle = component.type === 'title';
  return (
    <div
      style={{
        fontSize: isTitle ? 62 : 38,
        fontWeight: isTitle ? 950 : 800,
        lineHeight: 1.12,
        textAlign: 'center',
        letterSpacing: isTitle ? '-0.07em' : '-0.04em',
        color: isTitle ? theme.ink : colors.color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 14,
        textWrap: 'balance',
        ...style
      }}
    >
      <Icon name={component.icon} size={isTitle ? 46 : 34} color={colors.accent} />
      <span>{component.text}</span>
    </div>
  );
};
