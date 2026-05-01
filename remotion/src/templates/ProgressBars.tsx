import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

const parseItems = (text?: string) =>
  (text || '规划:82;组件:76;渲染:90')
    .split(';')
    .map((item) => {
      const [label, value] = item.split(':');
      return {label: label?.trim() || '指标', value: Number.parseFloat(value || '0') || 0};
    })
    .slice(0, 4);

export const ProgressBars: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'success');
  const items = parseItems(component.text);

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '30px 34px',
        display: 'flex',
        flexDirection: 'column',
        gap: 20,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {items.map((item, index) => {
        const progress = interpolate(frame - index * 8, [0, fps], [0, item.value], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp'
        });
        return (
          <div key={item.label} style={{display: 'flex', flexDirection: 'column', gap: 8}}>
            <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 24, fontWeight: 850, color: theme.ink}}>
              <span>{item.label}</span>
              <span style={{color: colors.accent}}>{Math.round(progress)}%</span>
            </div>
            <div style={{height: 14, borderRadius: 999, background: 'rgba(100,116,139,0.13)', overflow: 'hidden'}}>
              <div
                style={{
                  width: `${progress}%`,
                  height: '100%',
                  borderRadius: 999,
                  background: `linear-gradient(90deg, ${colors.accent}, rgba(14,165,233,0.55))`
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
