import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

export const HighlightText: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'warning');
  const words = (component.text || '结构化;稳定;可控').split(';').filter(Boolean).slice(0, 6);
  const framesPerWord = fps * 0.45;

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '28px 34px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 14,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {words.map((word, index) => {
        const progress = interpolate(frame, [index * framesPerWord, index * framesPerWord + framesPerWord * 0.75], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp'
        });
        return (
          <span key={word} style={{position: 'relative', padding: '6px 12px', fontSize: 34, fontWeight: 950, letterSpacing: '-0.06em', color: theme.ink}}>
            <span style={{position: 'absolute', inset: 0, borderRadius: 12, background: colors.background, transform: `scaleX(${progress})`, transformOrigin: 'left', opacity: 0.9}} />
            <span style={{position: 'relative'}}>{word}</span>
          </span>
        );
      })}
    </div>
  );
};
