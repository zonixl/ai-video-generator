import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {RemotionSceneSpec} from '../schema';
import {Canvas} from '../components/Canvas';
import {TextBlock} from '../components/TextBlock';
import {BackgroundPattern} from '../templates/BackgroundPattern';
import {FloatingShapes} from '../templates/FloatingShapes';
import {GridPulse} from '../templates/GridPulse';
import {resolveSceneLayout} from './layoutEngine';
import {resolveMotionStyle} from './motionEngine';
import {renderRegistryComponent} from '../templates/registry';

export const BasicDiagram: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const resolved = resolveSceneLayout(scene);
  const titleComponent = {
    id: 'headline',
    type: 'title' as const,
    slot: 'title' as const,
    text: resolved.headline,
    motion: 'slide_in' as const
  };

  // Subtitle spring entrance — nearly instant, must sync with audio
  const subtitleDelay = 0.15 * fps;
  const subtitleSpring = spring({
    frame: frame - subtitleDelay,
    fps,
    config: {damping: 14, stiffness: 120, mass: 0.9},
  });

  return (
    <Canvas scene={scene}>
      <FloatingShapes />
      <GridPulse />
      {resolved.background ? <BackgroundPattern component={resolved.background} /> : null}
      <TextBlock
        component={titleComponent}
        style={{
          position: 'absolute',
          left: 120,
          top: 96,
          width: 840,
          zIndex: 30,
          ...resolveMotionStyle({component: titleComponent, frame, fps, order: 0, isTitle: true})
        }}
      />
      {resolved.items.map(({component, order, style}) => {
        const safeStyle: React.CSSProperties = {
          ...style,
          ...resolveMotionStyle({component, frame, fps, order})
        };
        return renderRegistryComponent({component, frame, fps, index: order, style: safeStyle});
      })}
      {resolved.subtitle ? (
        <div
          style={{
            position: 'absolute',
            left: 130,
            bottom: 110,
            width: 820,
            background: 'rgba(22,32,51,0.78)',
            color: '#fff',
            padding: '22px 32px',
            borderRadius: 26,
            fontSize: 32,
            fontWeight: 750,
            lineHeight: 1.3,
            textAlign: 'center',
            boxShadow: '0 18px 50px rgba(28,35,58,0.18)',
            backdropFilter: 'blur(16px)',
            opacity: Math.min(1, subtitleSpring * 1.1),
            transform: `translateY(${(1 - subtitleSpring) * 20}px)`,
            zIndex: 40,
          }}
        >
          {resolved.subtitle}
        </div>
      ) : null}
    </Canvas>
  );
};
