import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from '../components/Icon';
import {parseParts} from './templateUtils';

export const LowerThird: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'primary');
  const [title = '核心观点', subtitle = 'AI 结构化生成'] = parseParts(component, '核心观点|AI 结构化生成');
  const progress = spring({frame, fps, config: {damping: 18, stiffness: 110}});

  return (
    <div
      style={{
        borderRadius: 30,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.82)',
        boxShadow: theme.shadow,
        padding: '24px 30px',
        display: 'grid',
        gridTemplateColumns: '60px 1fr',
        gap: 18,
        alignItems: 'center',
        transform: `translateX(${(1 - progress) * -80}px)`,
        opacity: progress,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      <div style={{width: 60, height: 60, borderRadius: 22, background: colors.background, color: colors.accent, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Icon name={component.icon ?? 'sparkles'} size={32} />
      </div>
      <div>
        <div style={{fontSize: 34, fontWeight: 950, color: theme.ink, letterSpacing: '-0.06em'}}>{title}</div>
        <div style={{fontSize: 23, fontWeight: 850, color: theme.mutedInk, marginTop: 4}}>{subtitle}</div>
      </div>
    </div>
  );
};
