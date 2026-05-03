import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';

export const ImageFullScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const titleDelay = 0.1 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
  const subDelay = 0.4 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#111'}}>
      {imageUrl ? (
        <Img src={imageUrl} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
      ) : null}
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.65) 100%)'}} />
      <div style={{
        position: 'absolute', top: '25%', left: '50%', transform: `translate(-50%, -50%) translateY(${(1 - titleEnter) * 40}px)`,
        width: 900, textAlign: 'center',
        fontSize: 80, fontWeight: 900, color: '#fff', lineHeight: 1.2, letterSpacing: 2,
        textShadow: '0 4px 20px rgba(0,0,0,0.5), 0 0 40px rgba(0,0,0,0.3)',
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          padding: '40px 60px', background: 'linear-gradient(transparent, rgba(0,0,0,0.75))',
          zIndex: 10,
        }}>
          <div style={{
            fontSize: 36, color: '#fff', textAlign: 'center', lineHeight: 1.6, fontWeight: 500,
            textShadow: '0 2px 12px rgba(0,0,0,0.6)',
            opacity: Math.min(1, subEnter * 1.2),
            transform: `translateY(${(1 - subEnter) * 20}px)`,
          }}>
            {scene.subtitle}
          </div>
        </div>
      ) : null}
    </div>
  );
};
