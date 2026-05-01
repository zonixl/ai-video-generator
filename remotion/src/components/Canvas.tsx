import React from 'react';
import type {RemotionSceneSpec} from '../schema';
import {backgroundFor, theme} from '../styles/theme';

export const Canvas: React.FC<{
  scene: RemotionSceneSpec;
  children: React.ReactNode;
}> = ({scene, children}) => {
  const background = backgroundFor(scene);
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        background,
        fontFamily: theme.fontFamily,
        color: theme.ink
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(222,187,116,0.22) 1px, transparent 1px), linear-gradient(90deg, rgba(222,187,116,0.22) 1px, transparent 1px)',
          backgroundSize: '42px 42px',
          opacity: scene.theme === 'clean' ? 0.25 : 0.55
        }}
      />
      {children}
    </div>
  );
};
