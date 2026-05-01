import type {ComponentSpec} from '../schema';

const limits: Partial<Record<ComponentSpec['type'], number>> = {
  badge: 12,
  card: 18,
  metric: 18,
  step: 18,
  quote: 34,
  typewriter: 42,
  lower_third: 28,
  notification: 42,
  highlight_text: 24
};

const truncate = (value: string, limit: number) => {
  const clean = value.replace(/\s+/g, ' ').trim();
  return clean.length > limit ? `${clean.slice(0, Math.max(0, limit - 1))}…` : clean;
};

export const normalizeComponentText = (component: ComponentSpec): ComponentSpec => {
  const limit = limits[component.type];
  if (!limit || !component.text) {
    return component;
  }

  if (component.text.includes(';')) {
    return {
      ...component,
      text: component.text
        .split(';')
        .slice(0, component.type === 'notification' ? 3 : 4)
        .map((part) => truncate(part, limit))
        .join(';')
    };
  }

  if (component.text.includes('|')) {
    return {
      ...component,
      text: component.text
        .split('|')
        .map((part, index) => (index === 0 && /\d/.test(part) ? part : truncate(part, limit)))
        .join('|')
    };
  }

  return {...component, text: truncate(component.text, limit)};
};

export const normalizeHeadline = (headline: string) => truncate(headline, 24);
export const normalizeSubtitle = (subtitle?: string) => truncate(subtitle || '', 52);
