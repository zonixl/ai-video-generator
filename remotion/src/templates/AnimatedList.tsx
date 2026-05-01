import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from '../components/Icon';

export const AnimatedList: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'default');
  const items = (component.text || '输入文案;AI 规划;组件渲染').split(';').filter(Boolean).slice(0, 5);

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '28px 30px',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {items.map((item, index) => {
        const progress = spring({frame: frame - index * 7, fps, config: {damping: 18, stiffness: 110}});
        return (
          <div
            key={item}
            style={{
              display: 'grid',
              gridTemplateColumns: '44px 1fr',
              alignItems: 'center',
              gap: 14,
              opacity: progress,
              transform: `translateX(${(1 - progress) * -28}px)`
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 16,
                background: colors.background,
                color: colors.accent,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Icon name={component.icon ?? 'check'} size={25} />
            </div>
            <div style={{fontSize: 27, fontWeight: 850, color: theme.ink, letterSpacing: '-0.04em'}}>{item}</div>
          </div>
        );
      })}
    </div>
  );
};
