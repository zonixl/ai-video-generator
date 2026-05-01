import React from 'react';
import {interpolate, spring} from 'remotion';
import type {ComponentSpec} from '../schema';

const complexTypes = new Set<ComponentSpec['type']>([
  'bar_chart',
  'line_chart',
  'donut_chart',
  'comparison',
  'circular_progress',
  'progress_steps',
  'notification',
  'progress'
]);

export const resolveMotionStyle = ({
  component,
  frame,
  fps,
  order,
  isTitle = false
}: {
  component: ComponentSpec;
  frame: number;
  fps: number;
  order: number;
  isTitle?: boolean;
}): React.CSSProperties => {
  const delay = (isTitle ? 0.18 : 0.58 + order * 0.32) * fps;
  const duration = (complexTypes.has(component.type) ? 0.9 : 0.58) * fps;
  const progress = spring({
    frame: frame - delay,
    fps,
    config: {damping: 22, stiffness: 82, mass: 0.92}
  });
  const fade = interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  if (component.motion === 'none') {
    return {};
  }
  if (component.motion === 'slide_in') {
    return {opacity: fade, transform: `translateY(${(1 - progress) * 28}px)`};
  }
  if (component.motion === 'pop') {
    return {opacity: fade, transform: `scale(${0.96 + progress * 0.04})`};
  }
  if (component.motion === 'pulse') {
    const pulse = 1 + Math.sin(Math.max(0, frame - delay) / 18) * 0.012;
    return {opacity: fade, transform: `scale(${pulse})`};
  }
  return {opacity: fade, transform: `translateY(${(1 - progress) * 16}px)`};
};
