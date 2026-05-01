import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec, ComponentSlot, RemotionSceneSpec} from '../schema';
import {Canvas} from '../components/Canvas';
import {TextBlock} from '../components/TextBlock';
import {BackgroundPattern} from '../templates/BackgroundPattern';
import {GridPulse} from '../templates/GridPulse';
import {renderRegistryComponent} from '../templates/registry';

const slotStyles: Record<ComponentSlot, React.CSSProperties> = {
  title: {left: 130, top: 150, width: 820},
  left_top: {left: 150, top: 430, width: 360},
  left_bottom: {left: 150, top: 610, width: 360},
  right_top: {left: 570, top: 430, width: 360},
  right_bottom: {left: 570, top: 610, width: 360},
  center: {left: 451, top: 525, width: 178},
  bottom: {left: 230, top: 830, width: 620},
  caption: {left: 130, bottom: 120, width: 820}
};

const motionStyle = (component: ComponentSpec, frame: number, fps: number, index: number): React.CSSProperties => {
  const delay = 8 + index * 8;
  const progress = spring({frame: frame - delay, fps, config: {damping: 16, stiffness: 120}});
  if (component.motion === 'slide_in') {
    return {opacity: progress, transform: `translateY(${(1 - progress) * 40}px)`};
  }
  if (component.motion === 'pop') {
    return {opacity: progress, transform: `scale(${0.88 + progress * 0.12})`};
  }
  if (component.motion === 'pulse') {
    const scale = 1 + Math.sin(frame / 8) * 0.025;
    return {opacity: progress, transform: `scale(${scale})`};
  }
  return {opacity: interpolate(frame, [delay, delay + 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})};
};

export const BasicDiagram: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <Canvas scene={scene}>
      <GridPulse />
      {scene.components.some((component) => component.type === 'background_pattern') ? (
        <BackgroundPattern component={scene.components.find((component) => component.type === 'background_pattern')} />
      ) : null}
      <TextBlock
        component={{id: 'headline', type: 'title', slot: 'title', text: scene.headline, motion: 'slide_in'}}
        style={{position: 'absolute' as const, ...slotStyles.title, ...motionStyle({id: 'headline', type: 'title', slot: 'title', motion: 'slide_in'}, frame, fps, 0)}}
      />
      {scene.components.map((component, index) => {
        const baseStyle: React.CSSProperties = {
          position: 'absolute',
          ...slotStyles[component.slot],
          ...motionStyle(component, frame, fps, index + 1)
        };
        if (component.type === 'background_pattern') {
          return null;
        }
        return renderRegistryComponent({component, frame, index, style: baseStyle});
      })}
      {scene.subtitle ? (
        <div
          style={{
            position: 'absolute',
            ...slotStyles.caption,
            background: 'rgba(22,32,51,0.78)',
            color: '#fff',
            padding: '22px 32px',
            borderRadius: 26,
            fontSize: 32,
            fontWeight: 750,
            lineHeight: 1.3,
            textAlign: 'center',
            boxShadow: '0 18px 50px rgba(28,35,58,0.18)',
            backdropFilter: 'blur(16px)'
          }}
        >
          {scene.subtitle}
        </div>
      ) : null}
    </Canvas>
  );
};
