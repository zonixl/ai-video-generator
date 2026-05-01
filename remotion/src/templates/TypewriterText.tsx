import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

export const TypewriterText: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'primary');
  const text = component.text || 'AI 输出 DSL，Remotion 负责稳定渲染。';
  const count = Math.floor(interpolate(frame, [0, fps * 1.8], [0, text.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '30px 34px',
        fontSize: 34,
        fontWeight: 850,
        color: theme.ink,
        lineHeight: 1.25,
        letterSpacing: '-0.04em',
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {text.slice(0, count)}
      <span style={{color: colors.accent}}>|</span>
    </div>
  );
};
