import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Arrow} from '../components/Arrow';
import {Badge} from '../components/Badge';
import {Canvas} from '../components/Canvas';
import {Card} from '../components/Card';
import {MetricCard} from '../components/MetricCard';
import {TextBlock} from '../components/TextBlock';
import {TimelineStep} from '../components/TimelineStep';
import {AnimatedList} from '../templates/AnimatedList';
import {ProgressBars} from '../templates/ProgressBars';
import {QuoteCard} from '../templates/QuoteCard';
import {StatCounter} from '../templates/StatCounter';
import type {RemotionSceneSpec} from '../schema';

const scene: RemotionSceneSpec = {
  scene_index: 1,
  duration: 8,
  template: 'basic_diagram',
  theme: 'warm_grid',
  headline: '组件库预览',
  subtitle: '',
  components: []
};

export const ComponentShowcase: React.FC = () => (
  <AbsoluteFill>
    <Canvas scene={scene}>
      <TextBlock
        component={{id: 'title', type: 'title', slot: 'title', text: 'Remotion 组件库', icon: 'sparkles'}}
        style={{position: 'absolute', left: 120, top: 90, width: 840}}
      />
      <Card
        component={{id: 'card', type: 'card', slot: 'left_top', text: '信息卡片', variant: 'primary', icon: 'brain'}}
        style={{position: 'absolute', left: 110, top: 260, width: 300}}
      />
      <MetricCard
        component={{id: 'metric', type: 'metric', slot: 'right_top', text: '81|模板能力', variant: 'warning', icon: 'target'}}
        style={{position: 'absolute', left: 440, top: 260, width: 310}}
      />
      <Badge
        component={{id: 'badge', type: 'badge', slot: 'bottom', text: '统一风格', variant: 'success', icon: 'check'}}
        style={{position: 'absolute', left: 790, top: 292, width: 190}}
      />
      <Arrow progress={1} label="连接" style={{position: 'absolute', left: 452, top: 470}} />
      <TimelineStep
        component={{id: 'step', type: 'step', slot: 'left_bottom', text: 'AI 只选择受控组件', variant: 'default', icon: 'workflow'}}
        style={{position: 'absolute', left: 110, top: 570, width: 380}}
      />
      <StatCounter
        component={{id: 'counter', type: 'stat_counter', slot: 'right_bottom', text: '92|GitHub stars|+', variant: 'primary', icon: 'zap'}}
        style={{position: 'absolute', left: 540, top: 570, width: 420}}
      />
      <ProgressBars
        component={{id: 'progress', type: 'progress', slot: 'bottom', text: '规划:82;组件:76;渲染:90', variant: 'success'}}
        style={{position: 'absolute', left: 110, top: 810, width: 410}}
      />
      <AnimatedList
        component={{id: 'list', type: 'list', slot: 'bottom', text: '输入文案;结构化 DSL;Remotion 渲染', variant: 'muted', icon: 'check'}}
        style={{position: 'absolute', left: 560, top: 810, width: 410}}
      />
      <QuoteCard
        component={{id: 'quote', type: 'quote', slot: 'caption', text: '模板能力本地化，AI 只做选择|受控组件库', variant: 'warning', icon: 'layers'}}
        style={{position: 'absolute', left: 140, top: 1190, width: 800}}
      />
    </Canvas>
  </AbsoluteFill>
);
