import type {ComponentVariant, RemotionSceneSpec} from '../schema';

export const theme = {
  fontFamily: '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif',
  ink: '#1f2933',
  paper: '#fbf3df',
  grid: 'rgba(222, 187, 116, 0.22)',
  shadow: 'rgba(24, 24, 24, 0.18)'
};

export const variantStyle = (variant: ComponentVariant = 'default') => {
  const variants: Record<ComponentVariant, {background: string; border: string; color: string}> = {
    default: {background: '#ffffff', border: '#202124', color: '#202124'},
    primary: {background: '#70d6ff', border: '#202124', color: '#12303c'},
    success: {background: '#49c7c8', border: '#202124', color: '#102f30'},
    danger: {background: '#ff7a70', border: '#202124', color: '#381311'},
    warning: {background: '#ffd76a', border: '#202124', color: '#3f3000'},
    muted: {background: '#eceff4', border: '#202124', color: '#30343b'}
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
