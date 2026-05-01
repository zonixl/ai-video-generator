import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {BasicDiagram} from '../layouts/BasicDiagram';
import type {RemotionSceneSpec} from '../schema';

const scenes: RemotionSceneSpec[] = [
  {
    scene_index: 1,
    duration: 3.5,
    template: 'basic_diagram',
    theme: 'warm_grid',
    layout: 'top_title_bottom_chart',
    headline: '数据模板',
    subtitle: '复杂图表独占主区域，避免和其他组件挤在一起。',
    components: [
      {id: 'bg', type: 'background_pattern', slot: 'caption', variant: 'primary', motion: 'none'},
      {id: 'bar', type: 'bar_chart', slot: 'left_top', text: '规划:72;执行:88;渲染:64;复盘:80', variant: 'primary', motion: 'pop'},
      {id: 'badge', type: 'badge', slot: 'left_bottom', text: '安全布局', variant: 'success', motion: 'slide_in', icon: 'check'},
      {id: 'metric', type: 'metric', slot: 'right_bottom', text: '1个|复杂模板', variant: 'warning', motion: 'slide_in', icon: 'target'}
    ]
  },
  {
    scene_index: 2,
    duration: 3.5,
    template: 'basic_diagram',
    theme: 'clean',
    layout: 'top_title_bottom_chart',
    headline: '趋势模板',
    subtitle: '折线图和说明组件分区渲染，动画节奏更慢。',
    components: [
      {id: 'line', type: 'line_chart', slot: 'right_top', text: '一:30;二:48;三:62;四:78;五:92', variant: 'success', motion: 'slide_in'},
      {id: 'lower', type: 'lower_third', slot: 'left_bottom', text: '趋势上升|只保留一个复杂图表', variant: 'primary', motion: 'slide_in', icon: 'workflow'}
    ]
  },
  {
    scene_index: 3,
    duration: 3.5,
    template: 'basic_diagram',
    theme: 'warm_grid',
    layout: 'timeline_vertical',
    headline: '文本与流程模板',
    subtitle: '强调词、打字机、步骤条和通知堆叠适合口播图示镜头。',
    components: [
      {id: 'highlight', type: 'highlight_text', slot: 'left_top', text: '结构化;稳定;多样化', variant: 'warning', motion: 'pop'},
      {id: 'typewriter', type: 'typewriter', slot: 'right_top', text: 'AI 只输出受控 DSL，Remotion 负责稳定动画。', variant: 'primary', motion: 'fade_in'},
      {id: 'steps', type: 'progress_steps', slot: 'bottom', text: '文案;规划;组件;渲染', variant: 'success', motion: 'slide_in'}
    ]
  },
  {
    scene_index: 4,
    duration: 3.5,
    template: 'basic_diagram',
    theme: 'warm_grid',
    layout: 'quote_focus',
    headline: '图示包装模板',
    subtitle: '下三分之一、引用卡和圆形进度用于增强镜头层次。',
    components: [
      {id: 'lower', type: 'lower_third', slot: 'left_top', text: '模板注册表|type -> component', variant: 'primary', motion: 'slide_in', icon: 'workflow'},
      {id: 'quote', type: 'quote', slot: 'bottom', text: '模板越多，越需要受控选择|Remotion DSL', variant: 'warning', motion: 'slide_in', icon: 'layers'},
      {id: 'circle', type: 'circular_progress', slot: 'right_top', text: '92|渲染通过率', variant: 'success', motion: 'pop'}
    ]
  },
  {
    scene_index: 5,
    duration: 3.5,
    template: 'basic_diagram',
    theme: 'clean',
    layout: 'top_title_bottom_chart',
    headline: '对比模板',
    subtitle: '前后对比独占主区域，避免遮住标题和字幕。',
    components: [
      {id: 'compare', type: 'comparison', slot: 'right_bottom', text: '旧方案|34|新方案|89', variant: 'success', motion: 'slide_in'},
      {id: 'notice', type: 'notification', slot: 'left_bottom', text: '布局已归一;动画已降速;文本已截断', variant: 'success', motion: 'pop'}
    ]
  }
];

export const TemplateShowcase: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill>
      {scenes.map((scene) => {
        const durationInFrames = Math.round(scene.duration * 30);
        const sequence = (
          <Sequence key={scene.scene_index} from={from} durationInFrames={durationInFrames}>
            <BasicDiagram scene={scene} />
          </Sequence>
        );
        from += durationInFrames;
        return sequence;
      })}
    </AbsoluteFill>
  );
};
