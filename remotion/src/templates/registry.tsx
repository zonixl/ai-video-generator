import React from 'react';
import {interpolate} from 'remotion';
import {Arrow} from '../components/Arrow';
import {Badge} from '../components/Badge';
import {Card} from '../components/Card';
import {MetricCard} from '../components/MetricCard';
import {TextBlock} from '../components/TextBlock';
import {TimelineStep} from '../components/TimelineStep';
import type {ComponentSpec} from '../schema';
import {AnimatedList} from './AnimatedList';
import {BarChart} from './BarChart';
import {CircularProgress} from './CircularProgress';
import {ComparisonChart} from './ComparisonChart';
import {DonutChart} from './DonutChart';
import {HighlightText} from './HighlightText';
import {LineChart} from './LineChart';
import {LowerThird} from './LowerThird';
import {NotificationPop} from './NotificationPop';
import {ProgressBars} from './ProgressBars';
import {ProgressSteps} from './ProgressSteps';
import {QuoteCard} from './QuoteCard';
import {StatCounter} from './StatCounter';
import {TypewriterText} from './TypewriterText';

export const templateTypes = [
  'bar_chart',
  'line_chart',
  'donut_chart',
  'comparison',
  'circular_progress',
  'highlight_text',
  'typewriter',
  'progress_steps',
  'notification',
  'lower_third',
  'stat_counter',
  'progress',
  'list',
  'quote'
];

export const renderRegistryComponent = ({
  component,
  frame,
  index,
  style
}: {
  component: ComponentSpec;
  frame: number;
  index: number;
  style: React.CSSProperties;
}) => {
  if (component.type === 'arrow') {
    const progress = interpolate(frame, [18 + index * 8, 38 + index * 8], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp'
    });
    return <Arrow key={component.id} progress={progress} label={component.text} style={style} />;
  }
  if (component.type === 'badge') return <Badge key={component.id} component={component} style={style} />;
  if (component.type === 'metric') return <MetricCard key={component.id} component={component} style={style} />;
  if (component.type === 'step') return <TimelineStep key={component.id} component={component} style={style} />;
  if (component.type === 'stat_counter') return <StatCounter key={component.id} component={component} style={style} />;
  if (component.type === 'progress') return <ProgressBars key={component.id} component={component} style={style} />;
  if (component.type === 'list') return <AnimatedList key={component.id} component={component} style={style} />;
  if (component.type === 'quote') return <QuoteCard key={component.id} component={component} style={style} />;
  if (component.type === 'bar_chart') return <BarChart key={component.id} component={component} style={style} />;
  if (component.type === 'line_chart') return <LineChart key={component.id} component={component} style={style} />;
  if (component.type === 'donut_chart') return <DonutChart key={component.id} component={component} style={style} />;
  if (component.type === 'comparison') return <ComparisonChart key={component.id} component={component} style={style} />;
  if (component.type === 'circular_progress') return <CircularProgress key={component.id} component={component} style={style} />;
  if (component.type === 'highlight_text') return <HighlightText key={component.id} component={component} style={style} />;
  if (component.type === 'typewriter') return <TypewriterText key={component.id} component={component} style={style} />;
  if (component.type === 'progress_steps') return <ProgressSteps key={component.id} component={component} style={style} />;
  if (component.type === 'notification') return <NotificationPop key={component.id} component={component} style={style} />;
  if (component.type === 'lower_third') return <LowerThird key={component.id} component={component} style={style} />;
  if (component.type === 'text' || component.type === 'title') return <TextBlock key={component.id} component={component} style={style} />;

  return (
    <div key={component.id} style={style}>
      <Card component={component} />
      {component.motion === 'strike' ? (
        <div
          style={{
            position: 'absolute',
            left: -20,
            right: -20,
            top: '50%',
            height: 6,
            borderRadius: 999,
            background: 'linear-gradient(90deg, rgba(239,68,68,0.2), #ef4444, rgba(239,68,68,0.2))',
            transform: 'rotate(-2deg)',
            boxShadow: '0 8px 22px rgba(239,68,68,0.24)'
          }}
        />
      ) : null}
    </div>
  );
};
