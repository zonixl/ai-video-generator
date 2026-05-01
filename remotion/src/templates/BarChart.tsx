import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';
import {clampPercent, parseChartItems} from './templateUtils';

export const BarChart: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'primary');
  const items = parseChartItems(component.text).slice(0, 5);

  return (
    <div
      style={{
        height: 250,
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '28px 30px',
        display: 'flex',
        alignItems: 'end',
        justifyContent: 'space-between',
        gap: 16,
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {items.map((item, index) => {
        const value = interpolate(frame - index * 6, [0, fps], [0, clampPercent(item.value)], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp'
        });
        return (
          <div key={item.label} style={{flex: 1, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'end', gap: 10}}>
            <div style={{fontSize: 22, fontWeight: 900, color: colors.accent, textAlign: 'center'}}>{Math.round(value)}</div>
            <div style={{height: 138, display: 'flex', alignItems: 'end'}}>
              <div
                style={{
                  width: '100%',
                  height: `${value}%`,
                  minHeight: 10,
                  borderRadius: 14,
                  background: `linear-gradient(180deg, ${colors.accent}, rgba(14,165,233,0.38))`
                }}
              />
            </div>
            <div style={{fontSize: 20, fontWeight: 800, color: theme.mutedInk, textAlign: 'center'}}>{item.label}</div>
          </div>
        );
      })}
    </div>
  );
};
