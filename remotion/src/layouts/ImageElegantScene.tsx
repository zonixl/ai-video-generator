import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';

export const ImageElegantScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const imgEnter = spring({frame, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});
  const titleDelay = 0.25 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
  const subDelay = 0.5 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#f5f0e8'}}>
      {/* Gradient orbs */}
      <div style={{position: 'absolute', width: 700, height: 700, borderRadius: '50%', background: 'radial-gradient(circle, rgba(165,180,252,0.4), transparent 70%)', top: -280, left: -250, filter: 'blur(80px)'}} />
      <div style={{position: 'absolute', width: 550, height: 550, borderRadius: '50%', background: 'radial-gradient(circle, rgba(244,114,182,0.35), transparent 70%)', top: '40%', right: -200, filter: 'blur(90px)'}} />
      <div style={{position: 'absolute', width: 450, height: 450, borderRadius: '50%', background: 'radial-gradient(circle, rgba(196,181,253,0.38), transparent 70%)', bottom: -100, left: '20%', filter: 'blur(70px)'}} />

      {/* Image */}
      <div style={{
        position: 'absolute', top: '10%', left: '50%', transform: `translateX(-50%) scale(${0.8 + imgEnter * 0.2})`,
        width: 880, height: 660, borderRadius: 32, overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0,0,0,0.15)', opacity: imgEnter,
        zIndex: 5,
      }}>
        {imageUrl ? (
          <Img src={imageUrl} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <div style={{width: '100%', height: '100%', background: 'linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 50%, #a78bfa 100%)'}} />
        )}
      </div>

      {/* Title */}
      <div style={{
        position: 'absolute', top: '58%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - titleEnter) * 30}px)`,
        width: 880, textAlign: 'center',
        fontSize: 68, fontWeight: 800, color: '#1e1b4b', lineHeight: 1.2,
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>

      {/* Subtitle */}
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', top: '74%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - subEnter) * 20}px)`,
          width: 820, textAlign: 'center',
          fontSize: 34, color: '#4a4560', lineHeight: 1.7, fontWeight: 500,
          opacity: subEnter, zIndex: 10,
        }}>
          {scene.subtitle}
        </div>
      ) : null}
    </div>
  );
};
