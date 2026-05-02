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

/** Bouncier spring: lower damping → overshoot & settle */
const BOUNCE = {damping: 12, stiffness: 160, mass: 0.8};
/** Smooth spring for heavy/chart components */
const SMOOTH = {damping: 18, stiffness: 100, mass: 1.0};
/** Snappy spring for small badges/icons */
const SNAPPY = {damping: 14, stiffness: 200, mass: 0.6};

/** Stagger follows ease-out */
const staggerDelay = (order: number): number => {
  const base = 0.2;
  const step = 0.15;
  return base + order * step;
};

/** Deterministic pseudo-random based on component id */
const seedFromId = (id: string): number => {
  let h = 0;
  for (let i = 0; i < id.length; i++) {
    h = ((h << 5) - h) + id.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h) / 2147483647;
};

/** Continuous micro-float after entrance */
const microFloat = (frame: number, fps: number, seed: number): number => {
  const active = Math.max(0, frame - staggerDelay(0) * fps); // after entrance window
  if (active <= 0) return 0;
  return Math.sin((frame + seed * 240) / 60) * 1.6;
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
  const delay = (isTitle ? 0.1 : staggerDelay(order)) * fps;
  const motion = component.motion || 'fade_in';
  const seed = seedFromId(component.id);

  if (motion === 'none') {
    return {};
  }

  // ---- draw (line/arrow progressive reveal) ----
  if (motion === 'draw') {
    const drawProgress = spring({frame: frame - delay, fps, config: SNAPPY});
    return {
      opacity: interpolate(frame, [delay, delay + 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      clipPath: `inset(0 ${(1 - drawProgress) * 100}% 0 0)`,
    };
  }

  // ---- strike (negated/old — subtle fade) ----
  if (motion === 'strike') {
    const p = spring({frame: frame - delay, fps, config: SMOOTH});
    return {
      opacity: 0.55 + p * 0.45,
      transform: `scale(${0.92 + p * 0.06})`,
    };
  }

  // ---- pop (scale bounce, random start scale) ----
  if (motion === 'pop') {
    const p = spring({frame: frame - delay, fps, config: BOUNCE});
    const startScale = 0.82 + seed * 0.12; // random 0.82-0.94
    const floatY = microFloat(frame, fps, seed);
    return {
      opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `scale(${startScale + p * (1 - startScale)}) translateY(${floatY}px)`,
      filter: `blur(${(1 - p) * 4}px)`,
    };
  }

  // ---- slide_in (random direction) ----
  if (motion === 'slide_in') {
    const p = spring({frame: frame - delay, fps, config: BOUNCE});
    const dirIdx = Math.floor(seed * 4); // 0-3
    const floatY = microFloat(frame, fps, seed);
    const floatX = microFloat(frame + 120, fps, seed * 0.7);
    // 0: from top, 1: from right, 2: from bottom, 3: from left
    const dirs = [
      `translateY(${(1 - p) * -40}px)`,
      `translateX(${(1 - p) * 30}px)`,
      `translateY(${(1 - p) * 30}px)`,
      `translateX(${(1 - p) * -30}px)`,
    ];
    return {
      opacity: interpolate(frame, [delay, delay + 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `${dirs[dirIdx]} translateY(${floatY}px) translateX(${floatX}px)`,
    };
  }

  // ---- pulse (continuous subtle heartbeat) ----
  if (motion === 'pulse') {
    const appear = spring({frame: frame - delay, fps, config: SMOOTH});
    const pulse = 1 + Math.sin(Math.max(0, frame - delay) / 14) * 0.022;
    return {
      opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      transform: `scale(${pulse * (0.94 + appear * 0.06)})`,
    };
  }

  // ---- fade_in (default, with micro lift + float) ----
  const p = spring({frame: frame - delay, fps, config: SMOOTH});
  const floatY = microFloat(frame, fps, seed);
  return {
    opacity: interpolate(frame, [delay, delay + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
    transform: `translateY(${(1 - p) * 10 + floatY}px)`,
  };
};
