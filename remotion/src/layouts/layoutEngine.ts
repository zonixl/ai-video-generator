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

/** 生成响应式 regions — 所有值按视频实际宽高比例计算 */
const buildRegions = (w: number, h: number): Record<string, React.CSSProperties> => {
  const pad = w * 0.11;          // 左右内边距
  const gap = w * 0.03;          // 列间距
  const col = (w - pad * 2 - gap) / 2;
  const topOffset = h * 0.22;    // 标题下方区域起始
  const rowH = h * 0.115;
  const rowGap = h * 0.02;

  return {
    left_top:    {left: pad,              top: topOffset,                          width: col, height: rowH},
    right_top:   {left: pad + col + gap,  top: topOffset,                          width: col, height: rowH},
    left_bottom: {left: pad,              top: topOffset + rowH + rowGap * 2,      width: col, height: rowH},
    right_bottom:{left: pad + col + gap,  top: topOffset + rowH + rowGap * 2,      width: col, height: rowH},
    center:      {left: w * 0.35,         top: topOffset + rowH + rowGap * 0.5,    width: w * 0.3, height: rowH * 0.4},
    bottom:      {left: pad,              top: h * 0.42,                           width: w - pad * 2, height: h * 0.095},
    v_top:       {left: w * 0.22,         top: topOffset,                          width: w * 0.56, height: rowH},
    v_mid:       {left: w * 0.35,         top: topOffset + rowH + rowGap,          width: w * 0.3, height: rowH * 0.4},
    v_bot:       {left: w * 0.22,         top: topOffset + rowH * 2 + rowGap * 2,  width: w * 0.56, height: rowH},
    wide_top:    {left: pad,              top: topOffset,                          width: w - pad * 2, height: h * 0.19},
    wide_middle: {left: pad,              top: h * 0.43,                           width: w - pad * 2, height: h * 0.16},
    wide_bottom: {left: pad,              top: h * 0.62,                           width: w - pad * 2, height: h * 0.13},
    focus:       {left: pad,              top: topOffset,                          width: w - pad * 2, height: h * 0.26},
    quote:       {left: pad,              top: h * 0.44,                           width: w - pad * 2, height: h * 0.14},
  };
};

export const resolveSceneLayout = (scene: RemotionSceneSpec, width?: number, height?: number): ResolvedScene => {
  const w = width ?? 1080;
  const h = height ?? 1920;
  const regions = buildRegions(w, h);
  const background = scene.components.find((component) => component.type === 'background_pattern');
  const layout = scene.layout ?? inferLayout(scene.components);
  const normalized = normalizeComponents(scene.components.filter((component) => component.type !== 'background_pattern'));
  const items = assignLayoutItems(normalized, layout, regions);

  return {
    headline: normalizeHeadline(scene.headline),
    subtitle: normalizeSubtitle(scene.subtitle),
    background,
    items
  };
};

const assignLayoutItems = (components: ComponentSpec[], layout: SceneLayout, regions: Record<string, React.CSSProperties>): LayoutItem[] => {
  const place = (comps: ComponentSpec[], slots: string[], orderOffset: number): LayoutItem[] =>
    comps.map((component, index) => ({
      component,
      order: orderOffset + index,
      style: {
        position: 'absolute' as const,
        ...(regions[slots[index] ?? slots[slots.length - 1]] ?? regions.bottom),
        boxSizing: 'border-box' as const,
        zIndex: 10 + orderOffset + index
      }
    }));

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
