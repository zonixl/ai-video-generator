import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ComponentSpec, ComponentSlot, RemotionSceneSpec} from '../schema';
import {Arrow} from '../components/Arrow';
import {Badge} from '../components/Badge';
import {Canvas} from '../components/Canvas';
import {Card} from '../components/Card';
import {TextBlock} from '../components/TextBlock';

const slotStyles: Record<ComponentSlot, React.CSSProperties> = {
  title: {left: 130, top: 150, width: 820},
  left_top: {left: 170, top: 430, width: 330},
  left_bottom: {left: 170, top: 600, width: 330},
  right_top: {left: 590, top: 430, width: 330},
  right_bottom: {left: 590, top: 600, width: 330},
  center: {left: 462, top: 520, width: 170},
  bottom: {left: 270, top: 800, width: 540},
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
        if (component.type === 'arrow') {
          const progress = interpolate(frame, [18 + index * 8, 38 + index * 8], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp'
          });
          return <Arrow key={component.id} progress={progress} style={baseStyle} />;
        }
        if (component.type === 'badge') {
          return <Badge key={component.id} component={component} style={baseStyle} />;
        }
        if (component.type === 'text' || component.type === 'title') {
          return <TextBlock key={component.id} component={component} style={baseStyle} />;
        }
        return (
          <div key={component.id} style={baseStyle}>
            <Card component={component} />
            {component.motion === 'strike' ? (
              <div
                style={{
                  position: 'absolute',
                  left: -20,
                  right: -20,
                  top: '50%',
                  height: 8,
                  background: '#202124',
                  transform: 'rotate(-2deg)'
                }}
              />
            ) : null}
          </div>
        );
      })}
      {scene.subtitle ? (
        <div
          style={{
            position: 'absolute',
            ...slotStyles.caption,
            background: 'rgba(0,0,0,0.68)',
            color: '#fff',
            padding: '20px 28px',
            borderRadius: 18,
            fontSize: 34,
            fontWeight: 700,
            lineHeight: 1.3,
            textAlign: 'center'
          }}
        >
          {scene.subtitle}
        </div>
      ) : null}
    </Canvas>
  );
};
