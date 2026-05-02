import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from './Icon';

export const Card: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const colors = variantStyle(component.variant);
  const isStrike = component.motion === 'strike';
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Strike-through line spring
  const strikeProgress = isStrike
    ? spring({frame: frame - 15, fps, config: {damping: 18, stiffness: 140, mass: 0.7}})
    : 0;

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
        position: 'relative',
        overflow: 'hidden',
        opacity: isStrike ? 0.72 : 1,
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

      {/* strike-through diagonal line */}
      {isStrike ? (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '-20%',
            width: '140%',
            height: 5,
            background: `linear-gradient(90deg, transparent, ${colors.accent}, transparent)`,
            borderRadius: 999,
            transform: `translateY(-50%) rotate(-12deg) scaleX(${strikeProgress})`,
            transformOrigin: 'left center',
            opacity: 0.8,
            pointerEvents: 'none',
          }}
        />
      ) : null}
    </div>
  );
};
