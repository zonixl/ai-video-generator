import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec} from '../schema';
import {theme, variantStyle} from '../styles/theme';

export const ProgressSteps: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = variantStyle(component.variant ?? 'primary');
  const steps = (component.text || '输入;规划;渲染;发布').split(';').filter(Boolean).slice(0, 5);
  const framesPerStep = fps * 0.45;

  return (
    <div
      style={{
        borderRadius: 34,
        border: `1.5px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.76)',
        boxShadow: theme.shadow,
        padding: '34px 26px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backdropFilter: 'blur(18px)',
        ...style
      }}
    >
      {steps.map((step, index) => {
        const active = interpolate(frame, [index * framesPerStep, index * framesPerStep + framesPerStep], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp'
        });
        const scale = spring({frame: frame - index * framesPerStep, fps, config: {damping: 14, stiffness: 120}});
        return (
          <React.Fragment key={step}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
              <div style={{width: 50, height: 50, borderRadius: 18, background: active > 0.55 ? colors.accent : 'rgba(100,116,139,0.14)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, fontWeight: 950, transform: `scale(${0.9 + scale * 0.1})`}}>{index + 1}</div>
              <div style={{fontSize: 20, fontWeight: 850, color: theme.ink}}>{step}</div>
            </div>
            {index < steps.length - 1 ? <div style={{width: 34, height: 3, borderRadius: 999, background: active > 0.85 ? colors.accent : 'rgba(100,116,139,0.16)', margin: '0 4px 26px'}} /> : null}
          </React.Fragment>
        );
      })}
    </div>
  );
};
