import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';
import type {RemotionSceneSpec} from '../schema';

export const ImageCardScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const imageUrl = scene.image_url ? staticFile(scene.image_url) : '';

  const cardEnter = spring({frame, fps, config: {damping: 14, stiffness: 120, mass: 0.8}});
  const titleDelay = 0.2 * fps;
  const titleEnter = spring({frame: frame - titleDelay, fps, config: {damping: 14, stiffness: 130, mass: 0.7}});
  const subDelay = 0.45 * fps;
  const subEnter = spring({frame: frame - subDelay, fps, config: {damping: 16, stiffness: 100, mass: 0.9}});

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#eef2ff'}}>
      {/* Decorative shapes */}
      <div style={{position: 'absolute', width: 400, height: 400, borderRadius: '50%', border: '2px solid rgba(99,102,241,0.15)', top: -120, right: -80}} />
      <div style={{position: 'absolute', width: 300, height: 300, borderRadius: '50%', background: 'rgba(99,102,241,0.06)', bottom: 80, left: -80}} />
      <div style={{position: 'absolute', width: 200, height: 200, borderRadius: 24, border: '2px solid rgba(245,158,11,0.12)', transform: 'rotate(15deg)', top: '15%', right: '10%'}} />

      {/* Title */}
      <div style={{
        position: 'absolute', top: '12%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - titleEnter) * 30}px)`,
        width: 880, textAlign: 'center',
        fontSize: 64, fontWeight: 800, color: '#1e1b4b', lineHeight: 1.2,
        opacity: titleEnter, zIndex: 10,
      }}>
        {scene.headline}
      </div>

      {/* Card with image */}
      <div style={{
        position: 'absolute', top: '30%', left: '50%', transform: `translate(-50%, 0) scale(${0.85 + cardEnter * 0.15})`,
        width: 820, borderRadius: 28, overflow: 'hidden',
        background: '#fff', boxShadow: '0 20px 60px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.04)',
        opacity: cardEnter, zIndex: 5,
      }}>
        {imageUrl ? (
          <Img src={imageUrl} style={{width: '100%', height: 520, objectFit: 'cover'}} />
        ) : (
          <div style={{width: '100%', height: 520, background: 'linear-gradient(135deg, #dbeafe, #e0e7ff)'}} />
        )}
      </div>

      {/* Subtitle */}
      {scene.subtitle ? (
        <div style={{
          position: 'absolute', bottom: '12%', left: '50%', transform: `translate(-50%, 0) translateY(${(1 - subEnter) * 20}px)`,
          width: 800, textAlign: 'center',
          fontSize: 32, color: '#4a4560', lineHeight: 1.7, fontWeight: 500,
          opacity: subEnter, zIndex: 10,
        }}>
          {scene.subtitle}
        </div>
      ) : null}
    </div>
  );
};
