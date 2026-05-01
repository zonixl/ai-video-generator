import type {ComponentVariant, RemotionSceneSpec} from '../schema';

export const theme = {
  fontFamily: '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif',
  ink: '#162033',
  mutedInk: '#607086',
  paper: '#f7f3ea',
  surface: 'rgba(255, 255, 255, 0.78)',
  grid: 'rgba(99, 102, 241, 0.09)',
  shadow: '0 22px 58px rgba(28, 35, 58, 0.14)',
  ring: 'rgba(255, 255, 255, 0.72)'
};

export const variantStyle = (variant: ComponentVariant = 'default') => {
  const variants: Record<ComponentVariant, {background: string; border: string; color: string; accent: string}> = {
    default: {background: 'rgba(255,255,255,0.82)', border: 'rgba(25,32,47,0.12)', color: '#162033', accent: '#64748b'},
    primary: {background: 'rgba(224,242,254,0.92)', border: 'rgba(14,165,233,0.24)', color: '#075985', accent: '#0ea5e9'},
    success: {background: 'rgba(220,252,231,0.9)', border: 'rgba(34,197,94,0.24)', color: '#166534', accent: '#22c55e'},
    danger: {background: 'rgba(254,226,226,0.9)', border: 'rgba(239,68,68,0.24)', color: '#991b1b', accent: '#ef4444'},
    warning: {background: 'rgba(254,243,199,0.94)', border: 'rgba(245,158,11,0.28)', color: '#92400e', accent: '#f59e0b'},
    muted: {background: 'rgba(241,245,249,0.86)', border: 'rgba(100,116,139,0.18)', color: '#334155', accent: '#64748b'}
  };
  return variants[variant];
};

export const backgroundFor = (scene: RemotionSceneSpec) => {
  if (scene.theme === 'dark_grid') {
    return '#111827';
  }
  if (scene.theme === 'clean') {
    return '#f8fafc';
  }
  return theme.paper;
};
