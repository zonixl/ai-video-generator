import React from 'react';
import {Composition, getInputProps} from 'remotion';
import {ComponentShowcase} from './compositions/ComponentShowcase';
import {DiagramVideo} from './compositions/DiagramVideo';
import {TemplateShowcase} from './compositions/TemplateShowcase';
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
        {id: 'a', type: 'card', slot: 'left_top', text: 'AI Plan', variant: 'primary', motion: 'pop', icon: 'brain'},
        {id: 'arrow', type: 'arrow', slot: 'center', text: '结构化', motion: 'draw'},
        {id: 'b', type: 'card', slot: 'right_top', text: 'Remotion', variant: 'success', motion: 'pop', icon: 'video'},
        {id: 'metric', type: 'metric', slot: 'left_bottom', text: 'MVP|可控组件', variant: 'warning', motion: 'slide_in', icon: 'target'},
        {id: 'badge', type: 'badge', slot: 'bottom', text: 'JSON -> Components -> Video', variant: 'warning', motion: 'slide_in', icon: 'workflow'}
      ]
    }
  ]
};

export const RemotionRoot: React.FC = () => {
  const props = getInputProps() as Partial<{spec: RemotionVideoSpec}> & Partial<RemotionVideoSpec>;
  const spec = props.spec ?? (props.scenes ? (props as RemotionVideoSpec) : fallbackSpec);
  const durationInFrames = Math.max(1, Math.ceil(spec.scenes.reduce((total, scene) => total + scene.duration, 0) * spec.fps));

  return (
    <>
    <Composition
      id="DiagramVideo"
      component={DiagramVideo}
      durationInFrames={durationInFrames}
      fps={spec.fps}
      width={spec.width}
      height={spec.height}
      defaultProps={{spec}}
    />
    <Composition
      id="ComponentShowcase"
      component={ComponentShowcase}
      durationInFrames={240}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="TemplateShowcase"
      component={TemplateShowcase}
      durationInFrames={525}
      fps={30}
      width={1080}
      height={1920}
    />
    </>
  );
};
