import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {Icon} from '../components/Icon';

export const NotificationPop: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'success');
  const items = (component.text || '已生成分镜;组件匹配完成;开始渲染').split(';').filter(Boolean).slice(0, 3);

  return (
    <div style={{position: 'relative', height: 220, ...style}}>
      {items.map((item, index) => {
        const progress = spring({frame: frame - index * 12, fps, config: {damping: 16, stiffness: 110}});
        return (
          <div
            key={item}
            style={{
              position: 'absolute',
              left: index * 24,
              right: 0,
              top: index * 58,
              borderRadius: 26,
              border: `1.5px solid ${colors.border}`,
              background: 'rgba(255,255,255,0.82)',
              boxShadow: theme.shadow,
              padding: '18px 22px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              opacity: progress,
              transform: `translateY(${(1 - progress) * 34}px)`,
              backdropFilter: 'blur(18px)'
            }}
          >
            <Icon name={component.icon ?? 'check'} size={26} color={colors.accent} />
            <span style={{fontSize: 24, fontWeight: 850, color: theme.ink}}>{item}</span>
          </div>
        );
      })}
    </div>
  );
};
