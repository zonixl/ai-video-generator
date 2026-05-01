import React from 'react';
import {Composition, getInputProps} from 'remotion';
import {DiagramVideo} from './compositions/DiagramVideo';
import type {RemotionVideoSpec} from './schema';

const fallbackSpec: RemotionVideoSpec = {
  title: 'Remotion Diagram',
  width: 1080,
  height: 1920,
  fps: 30,
  scenes: [
    {
      scene_index: 1,
      duration: 5,
      template: 'basic_diagram',
      theme: 'warm_grid',
      headline: 'Remotion 图示流程',
      subtitle: '这是最小可用 Remotion 渲染。',
      components: [
        {id: 'a', type: 'card', slot: 'left_top', text: 'AI Plan', variant: 'primary', motion: 'pop'},
        {id: 'arrow', type: 'arrow', slot: 'center', motion: 'draw'},
        {id: 'b', type: 'card', slot: 'right_top', text: 'Remotion', variant: 'success', motion: 'pop'},
        {id: 'badge', type: 'badge', slot: 'bottom', text: 'JSON -> Components -> Video', variant: 'warning', motion: 'slide_in'}
      ]
    }
  ]
};

export const RemotionRoot: React.FC = () => {
  const props = getInputProps() as Partial<{spec: RemotionVideoSpec}> & Partial<RemotionVideoSpec>;
  const spec = props.spec ?? (props.scenes ? (props as RemotionVideoSpec) : fallbackSpec);
  const durationInFrames = Math.max(1, Math.ceil(spec.scenes.reduce((total, scene) => total + scene.duration, 0) * spec.fps));

  return (
    <Composition
      id="DiagramVideo"
      component={DiagramVideo}
      durationInFrames={durationInFrames}
      fps={spec.fps}
      width={spec.width}
      height={spec.height}
      defaultProps={{spec}}
    />
  );
};
