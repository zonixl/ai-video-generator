import React from 'react';
import {spring, interpolate, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';
import {responsive} from './responsive';

export const ImageNeonScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const r = responsive(width, height);
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const pulse = 0.85 + Math.sin(frame / 40) * 0.15;
  const imgEnter = spring({frame, fps, config: {damping: 14, stiffness: 140, mass: 0.7}});
  const titleDelay = 0.25 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 12, stiffness: 160, mass: 0.6}});
  const subDelay = 0.5 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});
  const glowDelay = 0.8 * fps;
  const glowIntensity = interpolate(frame - glowDelay, [0, 20], [0, 1], {extrapolateRight: 'clamp'});
  const imgHeight = Math.round(Math.min(r.cardWidth * 0.67, height * 0.45));

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#0a0a1a'}}>
      {/* Neon orbs */}
      <div style={{position: 'absolute', width: r.orbSize * 0.71, height: r.orbSize * 0.71, borderRadius: '50%', background: 'radial-gradient(circle, rgba(236,72,153,0.4), transparent 70%)', top: -r.orbSize * 0.21, left: -r.orbSize * 0.14, filter: 'blur(60px)', opacity: pulse}} />
      <div style={{position: 'absolute', width: r.orbSize * 0.85, height: r.orbSize * 0.85, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.35), transparent 70%)', bottom: -r.orbSize * 0.28, right: -r.orbSize * 0.21, filter: 'blur(70px)', opacity: pulse}} />
      <div style={{position: 'absolute', width: r.orbSize * 0.42, height: r.orbSize * 0.42, borderRadius: '50%', background: 'radial-gradient(circle, rgba(168,85,247,0.3), transparent 70%)', top: '50%', left: '60%', filter: 'blur(50px)', opacity: pulse * 0.8}} />

      {/* Image */}
      <div style={{
        position: 'absolute', top: '10%', left: '50%', transform: `translateX(-50%) scale(${0.85 + imgEnter * 0.15})`,
        width: r.cardWidth, height: imgHeight, borderRadius: r.borderRadius, overflow: 'hidden',
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
        width: r.titleWidth, textAlign: 'center',
        fontSize: r.titleFontSize, fontWeight: 900, color: '#fff', lineHeight: 1.2,
        textShadow: `0 0 ${10 + glowIntensity * 20}px rgba(236,72,153,0.6), 0 0 ${20 + glowIntensity * 40}px rgba(6,182,212,0.3)`,
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>

      {/* Subtitle */}
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', top: '78%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - subEnter) * 20}px)`,
          width: r.subtitleWidth, textAlign: 'center',
          fontSize: r.subtitleFontSize, color: 'rgba(255,255,255,0.7)', lineHeight: 1.6, fontWeight: 400,
          opacity: subEnter, zIndex: 10,
        }}>
          {scene.subtitle}
        </div>
      ) : null}
    </div>
  );
};
