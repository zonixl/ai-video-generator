import React from 'react';
import {useCurrentFrame} from 'remotion';
import type {RemotionSceneSpec} from '../schema';
import {backgroundFor, theme} from '../styles/theme';

export const Canvas: React.FC<{
  scene: RemotionSceneSpec;
  children: React.ReactNode;
}> = ({scene, children}) => {
  const frame = useCurrentFrame();
  const background = backgroundFor(scene);
  // breathe: slow background gradient pulse over ~6 seconds
  const breathe = 1 + Math.sin(frame / 90) * 0.06;
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        background,
        fontFamily: theme.fontFamily,
        color: theme.ink,
        backgroundImage:
          scene.theme === 'dark_grid'
            ? `radial-gradient(circle at 30% 18%, rgba(59,130,246,${0.24 * breathe}), transparent 34%), radial-gradient(circle at 78% 24%, rgba(168,85,247,${0.18 * breathe}), transparent 30%)`
            : `radial-gradient(circle at 24% 18%, rgba(14,165,233,${0.16 * breathe}), transparent 34%), radial-gradient(circle at 82% 16%, rgba(245,158,11,${0.14 * breathe}), transparent 30%)`
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(99,102,241,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.09) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
          opacity: scene.theme === 'clean' ? 0.45 : 0.8
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 54,
          borderRadius: 48,
          border: `1px solid ${theme.ring}`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.68)',
          pointerEvents: 'none'
        }}
      />
      {children}
    </div>
  );
};
