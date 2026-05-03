import React from 'react';
import {spring, interpolate, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';

export const ImageNeonScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const pulse = 0.85 + Math.sin(frame / 40) * 0.15;
  const imgEnter = spring({frame, fps, config: {damping: 14, stiffness: 140, mass: 0.7}});
  const titleDelay = 0.25 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 12, stiffness: 160, mass: 0.6}});
  const subDelay = 0.5 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});
  const glowDelay = 0.8 * fps;
  const glowIntensity = interpolate(frame - glowDelay, [0, 20], [0, 1], {extrapolateRight: 'clamp'});

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#0a0a1a'}}>
      {/* Neon orbs */}
      <div style={{position: 'absolute', width: 500, height: 500, borderRadius: '50%', background: 'radial-gradient(circle, rgba(236,72,153,0.4), transparent 70%)', top: -150, left: -100, filter: 'blur(60px)', opacity: pulse}} />
      <div style={{position: 'absolute', width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.35), transparent 70%)', bottom: -200, right: -150, filter: 'blur(70px)', opacity: pulse}} />
      <div style={{position: 'absolute', width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(168,85,247,0.3), transparent 70%)', top: '50%', left: '60%', filter: 'blur(50px)', opacity: pulse * 0.8}} />

      {/* Image */}
      <div style={{
        position: 'absolute', top: '10%', left: '50%', transform: `translateX(-50%) scale(${0.85 + imgEnter * 0.15})`,
        width: 840, height: 560, borderRadius: 20, overflow: 'hidden',
        border: `2px solid rgba(236,72,153,${0.3 + glowIntensity * 0.4})`,
        boxShadow: `0 0 ${20 + glowIntensity * 30}px rgba(236,72,153,${0.2 + glowIntensity * 0.3}), 0 20px 60px rgba(0,0,0,0.4)`,
        opacity: imgEnter, zIndex: 5,
      }}>
        {imageUrl ? (
          <Img src={imageUrl} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <div style={{width: '100%', height: '100%', background: 'linear-gradient(135deg, #1a1a2e, #16213e, #0f3460)'}} />
        )}
      </div>

      {/* Title with neon glow */}
      <div style={{
        position: 'absolute', top: '60%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - titleEnter) * 40}px)`,
        width: 880, textAlign: 'center',
        fontSize: 76, fontWeight: 900, color: '#fff', lineHeight: 1.2,
        textShadow: `0 0 ${10 + glowIntensity * 20}px rgba(236,72,153,0.6), 0 0 ${20 + glowIntensity * 40}px rgba(6,182,212,0.3)`,
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>

      {/* Subtitle */}
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', top: '78%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - subEnter) * 20}px)`,
          width: 820, textAlign: 'center',
          fontSize: 30, color: 'rgba(255,255,255,0.7)', lineHeight: 1.6, fontWeight: 400,
          opacity: subEnter, zIndex: 10,
        }}>
          {scene.subtitle}
        </div>
      ) : null}
    </div>
  );
};
