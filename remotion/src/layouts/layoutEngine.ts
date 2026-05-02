import React from 'react';
import type {ComponentSpec, RemotionSceneSpec, SceneLayout} from '../schema';
import {normalizeComponentText, normalizeHeadline, normalizeSubtitle} from './textUtils';

export type LayoutItem = {
  component: ComponentSpec;
  style: React.CSSProperties;
  order: number;
};

export type ResolvedScene = {
  headline: string;
  subtitle: string;
  background?: ComponentSpec;
  items: LayoutItem[];
};

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

const regions: Record<string, React.CSSProperties> = {
  left_top: {left: 120, top: 430, width: 390, height: 220},
  right_top: {left: 570, top: 430, width: 390, height: 220},
  left_bottom: {left: 120, top: 850, width: 390, height: 220},
  right_bottom: {left: 570, top: 850, width: 390, height: 220},
  // arrow below both cards (two_column_compare) or between vertical items
  center: {left: 440, top: 670, width: 200, height: 70},
  bottom: {left: 150, top: 800, width: 780, height: 180},
  // vertical_flow: stacked top-to-bottom
  v_top: {left: 240, top: 440, width: 600, height: 170},
  v_mid: {left: 380, top: 630, width: 320, height: 70},
  v_bot: {left: 240, top: 720, width: 600, height: 170},
  // wide slots for timeline/chart layouts
  wide_top: {left: 140, top: 390, width: 800, height: 360},
  wide_middle: {left: 140, top: 820, width: 800, height: 300},
  wide_bottom: {left: 150, top: 1180, width: 780, height: 240},
  focus: {left: 150, top: 440, width: 780, height: 500},
  quote: {left: 150, top: 840, width: 780, height: 260}
};

export const resolveSceneLayout = (scene: RemotionSceneSpec): ResolvedScene => {
  const background = scene.components.find((component) => component.type === 'background_pattern');
  const layout = scene.layout ?? inferLayout(scene.components);
  const normalized = normalizeComponents(scene.components.filter((component) => component.type !== 'background_pattern'));
  const items = assignLayoutItems(normalized, layout);

  return {
    headline: normalizeHeadline(scene.headline),
    subtitle: normalizeSubtitle(scene.subtitle),
    background,
    items
  };
};

const assignLayoutItems = (components: ComponentSpec[], layout: SceneLayout): LayoutItem[] => {
  // vertical_flow: cards stacked top→bottom, arrow in between pointing down
  if (layout === 'vertical_flow') {
    const arrow = components.find((component) => component.type === 'arrow');
    const cards = components.filter((component) => component.type !== 'arrow' && component.type !== 'badge');
    const badges = components.filter((component) => component.type === 'badge');
    const result: LayoutItem[] = [];
    if (cards.length >= 1) result.push(...place(cards.slice(0, 1), ['v_top'], 0));
    if (arrow) result.push(...place([arrow], ['v_mid'], 1));
    if (cards.length >= 2) result.push(...place(cards.slice(1, 2), ['v_bot'], 2));
    result.push(...place(cards.slice(2).concat(badges), ['wide_bottom', 'bottom'], 3));
    return result.sort((a, b) => a.order - b.order);
  }

  if (layout === 'two_column_compare') {
    const arrow = components.find((component) => component.type === 'arrow');
    const others = components.filter((component) => component.type !== 'arrow');
    return [
      ...place(others.slice(0, 1), ['left_top'], 0),
      ...place(others.slice(1, 2), ['right_top'], 1),
      ...(arrow ? place([arrow], ['center'], 2) : []),
      ...place(others.slice(2), ['bottom'], 3)
    ].sort((a, b) => a.order - b.order);
  }

  if (layout === 'top_title_bottom_chart') {
    const complex = components.find((component) => complexTypes.has(component.type));
    const others = components.filter((component) => component !== complex);
    return [
      ...(complex ? place([complex], ['wide_top'], 0) : []),
      ...place(others, ['left_bottom', 'right_bottom', 'wide_bottom'], 1)
    ];
  }

  if (layout === 'timeline_vertical') {
    return place(components, ['wide_top', 'wide_middle', 'wide_bottom', 'bottom'], 0);
  }

  if (layout === 'quote_focus') {
    const quote = components.find((component) => component.type === 'quote');
    const lower = components.find((component) => component.type === 'lower_third');
    const others = components.filter((component) => component !== quote && component !== lower);
    return [
      ...(lower ? place([lower], ['wide_top'], 0) : []),
      ...(quote ? place([quote], ['quote'], 1) : []),
      ...place(others, ['wide_bottom', 'left_top', 'right_top'], 2)
    ];
  }

  if (layout === 'center_focus') {
    return place(components, ['focus', 'wide_bottom', 'left_bottom', 'right_bottom'], 0);
  }

  return place(components, ['left_top', 'right_top', 'left_bottom', 'right_bottom', 'bottom'], 0);
};

const place = (components: ComponentSpec[], slots: string[], orderOffset: number): LayoutItem[] =>
  components.map((component, index) => ({
    component,
    order: orderOffset + index,
    style: {
      position: 'absolute' as const,
      ...(regions[slots[index] ?? slots[slots.length - 1]] ?? regions.bottom),
      boxSizing: 'border-box' as const,
      zIndex: 10 + orderOffset + index
    }
  }));

const inferLayout = (components: ComponentSpec[]): SceneLayout => {
  if (components.some((component) => component.type === 'quote' || component.type === 'lower_third')) {
    return 'quote_focus';
  }
  if (components.some((component) => component.type === 'progress_steps' || component.type === 'list' || component.type === 'step')) {
    return 'timeline_vertical';
  }
  if (components.some((component) => ['bar_chart', 'line_chart', 'donut_chart', 'comparison', 'circular_progress', 'progress'].includes(component.type))) {
    return 'top_title_bottom_chart';
  }
  if (components.some((component) => component.type === 'arrow')) {
    return 'vertical_flow';  // use vertical flow by default when arrow present
  }
  return 'auto';
};

const normalizeComponents = (components: ComponentSpec[]) => {
  let hasComplex = false;
  const normalized: ComponentSpec[] = [];

  for (const component of components) {
    if (normalized.length >= 5) {
      break;
    }
    if (complexTypes.has(component.type)) {
      if (hasComplex) {
        continue;
      }
      hasComplex = true;
    }
    normalized.push(normalizeComponentText({...component, motion: normalizeMotion(component)}));
  }
  return normalized;
};

const normalizeMotion = (component: ComponentSpec) => {
  if (complexTypes.has(component.type)) {
    return component.motion === 'none' ? 'none' : 'slide_in';
  }
  if (component.motion === 'pulse') {
    return 'fade_in';
  }
  return component.motion ?? 'fade_in';
};
