import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';
import {responsive} from './responsive';

export const ImageModernScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const r = responsive(width, height);
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const breathe = 1 + Math.sin(frame / 90) * 0.05;
  const cardEnter = spring({frame, fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
  const titleDelay = 0.2 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 14, stiffness: 130, mass: 0.7}});
  const subDelay = 0.45 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});
  const cardImgHeight = Math.round(Math.min(r.cardWidth * 0.675, height * 0.45));

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#0f172a'}}>
      {/* Gradient orbs */}
      <div style={{position: 'absolute', width: r.orbSize * 0.85, height: r.orbSize * 0.85, borderRadius: '50%', background: 'radial-gradient(circle, rgba(59,130,246,0.35), transparent 70%)', top: -r.orbSize * 0.28, left: -r.orbSize * 0.21, filter: 'blur(80px)', opacity: breathe}} />
      <div style={{position: 'absolute', width: r.orbSize * 0.71, height: r.orbSize * 0.71, borderRadius: '50%', background: 'radial-gradient(circle, rgba(168,85,247,0.3), transparent 70%)', bottom: -r.orbSize * 0.21, right: -r.orbSize * 0.14, filter: 'blur(80px)', opacity: breathe}} />
      {/* Grid lines */}
      <div style={{position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(99,102,241,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.07) 1px, transparent 1px)', backgroundSize: '44px 44px'}} />

      {/* Title */}
      <div style={{
        position: 'absolute', top: '12%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - titleEnter) * 30}px)`,
        width: r.titleWidth, textAlign: 'center',
        fontSize: r.titleFontSize, fontWeight: 800, color: '#f1f5f9', lineHeight: 1.2,
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>

      {/* Glass card with image */}
      <div style={{
        position: 'absolute', top: '28%', left: '50%', transform: `translate(-50%, 0) scale(${0.88 + cardEnter * 0.12})`,
        width: r.cardWidth, borderRadius: r.borderRadius, overflow: 'hidden',
        background: 'rgba(255,255,255,0.06)', backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.1)',
        boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
        opacity: cardEnter, zIndex: 5,
      }}>
        {imageUrl ? (
          <Img src={imageUrl} style={{width: '100%', height: cardImgHeight, objectFit: 'cover'}} />
        ) : (
          <div style={{width: '100%', height: cardImgHeight, background: 'linear-gradient(135deg, #1e3a5f, #312e81)'}} />
        )}
      </div>

      {/* Subtitle */}
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', bottom: '12%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - subEnter) * 20}px)`,
          width: r.subtitleWidth, textAlign: 'center',
          fontSize: r.subtitleFontSize, color: 'rgba(255,255,255,0.85)', lineHeight: 1.7, fontWeight: 400,
          opacity: subEnter, zIndex: 10,
        }}>
          {scene.subtitle}
        </div>
      ) : null}
    </div>
  );
};
