import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import type {RemotionVideoSpec} from '../schema';
import {BasicDiagram} from '../layouts/BasicDiagram';
import {KineticTextScene} from '../layouts/KineticTextScene';
import {ImageFullScene} from '../layouts/ImageFullScene';
import {ImageElegantScene} from '../layouts/ImageElegantScene';
import {ImageCardScene} from '../layouts/ImageCardScene';
import {ImageModernScene} from '../layouts/ImageModernScene';
import {ImageNeonScene} from '../layouts/ImageNeonScene';
import {SketchCourseScene} from '../layouts/SketchCourseScene';

const renderScene = (scene: RemotionVideoSpec['scenes'][0]) => {
  switch (scene.template) {
    case 'kinetic_text':
      return <KineticTextScene scene={scene} />;
    case 'image_full':
      return <ImageFullScene scene={scene} />;
    case 'image_elegant':
      return <ImageElegantScene scene={scene} />;
    case 'image_card':
      return <ImageCardScene scene={scene} />;
    case 'image_modern':
      return <ImageModernScene scene={scene} />;
    case 'image_neon':
      return <ImageNeonScene scene={scene} />;
    case 'sketch_course':
      return <SketchCourseScene scene={scene} />;
    default:
      return <BasicDiagram scene={scene} />;
  }
};

export const DiagramVideo: React.FC<{spec: RemotionVideoSpec}> = ({spec}) => {
  let startFrame = 0;
  return (
    <AbsoluteFill style={{background: '#111'}}>
      {spec.audio_src ? (
        <Audio src={spec.audio_src.startsWith('http') ? spec.audio_src : staticFile(spec.audio_src)} />
      ) : null}
      {spec.scenes.map((scene) => {
        const durationFrames = Math.max(1, Math.round(scene.duration * spec.fps));
        const sceneElement = renderScene(scene);
        const sequence = (
          <Sequence key={scene.scene_index} from={startFrame} durationInFrames={durationFrames}>
            {sceneElement}
          </Sequence>
        );
        startFrame += durationFrames;
        return sequence;
      })}
    </AbsoluteFill>
  );
};
