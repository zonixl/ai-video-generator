import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import type {RemotionVideoSpec} from '../schema';
import {BasicDiagram} from '../layouts/BasicDiagram';

export const DiagramVideo: React.FC<{spec: RemotionVideoSpec}> = ({spec}) => {
  let startFrame = 0;
  return (
    <AbsoluteFill style={{background: '#fbf3df'}}>
      {spec.audio_src ? (
        <Audio src={spec.audio_src.startsWith('http') ? spec.audio_src : staticFile(spec.audio_src)} />
      ) : null}
      {spec.scenes.map((scene) => {
        const durationFrames = Math.max(1, Math.round(scene.duration * spec.fps));
        const sequence = (
          <Sequence key={scene.scene_index} from={startFrame} durationInFrames={durationFrames}>
            <BasicDiagram scene={scene} />
          </Sequence>
        );
        startFrame += durationFrames;
        return sequence;
      })}
    </AbsoluteFill>
  );
};
