import React from 'react';
import {
  AudioLines,
  Brain,
  Check,
  Code2,
  Image,
  Layers3,
  Settings2,
  Sparkles,
  Target,
  Video,
  Workflow,
  X,
  Zap
} from 'lucide-react';
import type {IconName} from '../schema';

const icons = {
  sparkles: Sparkles,
  brain: Brain,
  workflow: Workflow,
  image: Image,
  video: Video,
  audio: AudioLines,
  check: Check,
  x: X,
  zap: Zap,
  target: Target,
  layers: Layers3,
  code: Code2,
  settings: Settings2
};

export const Icon: React.FC<{
  name?: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}> = ({name, size = 34, color = 'currentColor', strokeWidth = 2.2}) => {
  if (!name) {
    return null;
  }
  const LucideIcon = icons[name];
  return <LucideIcon size={size} color={color} strokeWidth={strokeWidth} />;
};
