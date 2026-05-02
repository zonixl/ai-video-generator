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

/** Bouncier spring: lower damping → overshoot & settle, feels alive */
const BOUNCE = {damping: 12, stiffness: 160, mass: 0.8};
/** Smooth spring for heavy/chart components */
const SMOOTH = {damping: 18, stiffness: 100, mass: 1.0};
/** Snappy spring for small badges/icons */
const SNAPPY = {damping: 14, stiffness: 200, mass: 0.6};

/** Stagger follows ease-out — earlier elements get shorter delay, later ones wait more */
const staggerDelay = (order: number): number => {
  const base = 0.25;  // first component starts at 0.25s
  const step = 0.18;  // each subsequent +0.18s
  return base + order * step;
};

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
  const delay = (isTitle ? 0.12 : staggerDelay(order)) * fps;
  const motion = component.motion || 'fade_in';

  if (motion === 'none') {
    return {};
  }

  // ---- draw (line/arrow progressive reveal) ----
  if (motion === 'draw') {
    const drawProgress = spring({
      frame: frame - delay,
      fps,
      config: SNAPPY,
    });
    return {
      opacity: interpolate(frame, [delay, delay + 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      clipPath: `inset(0 ${(1 - drawProgress) * 100}% 0 0)`,
    };
  }

  // ---- strike (cross-out → appear) ----
  if (motion === 'strike') {
    const p = spring({frame: frame - delay, fps, config: SNAPPY});
    return {
      opacity: Math.min(1, p * 1.3),
      transform: `scale(${0.92 + p * 0.08}) rotate(${(1 - p) * 3}deg)`,
    };
  }

  // ---- pop (scale bounce) ----
  if (motion === 'pop') {
    const p = spring({frame: frame - delay, fps, config: BOUNCE});
    return {
      opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `scale(${0.88 + p * 0.12})`,
      filter: `blur(${(1 - p) * 4}px)`,
    };
  }

  // ---- slide_in ----
  if (motion === 'slide_in') {
    const p = spring({frame: frame - delay, fps, config: BOUNCE});
    return {
      opacity: interpolate(frame, [delay, delay + 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `translateY(${(1 - p) * 36}px)`,
    };
  }

  // ---- pulse (continuous subtle heartbeat) ----
  if (motion === 'pulse') {
    const appear = spring({frame: frame - delay, fps, config: SMOOTH});
    const pulse = 1 + Math.sin(Math.max(0, frame - delay) / 14) * 0.018;
    return {
      opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `scale(${pulse * (0.94 + appear * 0.06)})`,
    };
  }

  // ---- fade_in (default, with micro lift) ----
  const p = spring({frame: frame - delay, fps, config: SMOOTH});
  return {
    opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
    transform: `translateY(${(1 - p) * 12}px)`,
  };
};
