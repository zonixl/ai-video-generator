import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from '../components/Icon';

export const QuoteCard: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'warning');
  const [quote = component.text ?? '', author = '关键观点'] = (component.text ?? '').split('|');
  const progress = spring({frame, fps, config: {damping: 18, stiffness: 100}});

  return (
    <div
      style={{
        borderRadius: 38,
        border: `1.5px solid ${colors.border}`,
        background: colors.background,
        boxShadow: theme.shadow,
        padding: '34px 38px',
        color: colors.color,
        transform: `scale(${0.96 + progress * 0.04})`,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <div style={{color: colors.accent, marginBottom: 16}}>
        <Icon name={component.icon ?? 'sparkles'} size={38} />
      </div>
      <div style={{fontSize: 34, fontWeight: 900, lineHeight: 1.18, letterSpacing: '-0.05em'}}>
        “{quote}”
      </div>
      <div style={{marginTop: 18, fontSize: 24, fontWeight: 850, color: theme.mutedInk}}>{author}</div>
    </div>
  );
};
