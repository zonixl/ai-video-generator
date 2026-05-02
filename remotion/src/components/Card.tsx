import React from 'react';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const Card: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant);
  const isStrike = component.motion === 'strike';

  return (
    <div
      style={{
        minHeight: 92,
        borderRadius: 28,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        color: colors.color,
        boxShadow: theme.shadow,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        alignItems: 'center',
        justifyContent: 'center',
        padding: '28px 30px',
        fontSize: 34,
        fontWeight: 800,
        textAlign: 'center',
        lineHeight: 1.16,
        letterSpacing: '-0.04em',
        backdropFilter: 'blur(18px)',
        opacity: isStrike ? 0.68 : 1,
        ...style,
      }}
    >
      {component.icon ? (
        <div
          style={{
            width: 58,
            height: 58,
            borderRadius: 18,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255,255,255,0.62)',
            color: colors.accent,
          }}
        >
          <Icon name={component.icon} />
        </div>
      ) : null}
      <div>{component.text}</div>
    </div>
  );
};
