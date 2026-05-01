import type {ComponentSpec} from '../schema';

export type ChartItem = {
  label: string;
  value: number;
};

export const parseChartItems = (text?: string, fallback = '规划:72;执行:88;渲染:64;复盘:80'): ChartItem[] =>
  (text || fallback)
    .split(';')
    .map((item) => {
      const [label, value] = item.split(':');
      return {label: label?.trim() || '指标', value: Number.parseFloat(value || '0') || 0};
    })
    .filter((item) => Number.isFinite(item.value))
    .slice(0, 6);

export const parseParts = (component: ComponentSpec, fallback: string) => (component.text || fallback).split('|');

export const clampPercent = (value: number) => Math.max(0, Math.min(100, value));
