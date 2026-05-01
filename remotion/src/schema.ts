export type ComponentType =
  | 'title'
  | 'card'
  | 'arrow'
  | 'badge'
  | 'text'
  | 'metric'
  | 'step'
  | 'stat_counter'
  | 'progress'
  | 'list'
  | 'quote'
  | 'bar_chart'
  | 'line_chart'
  | 'donut_chart'
  | 'comparison'
  | 'circular_progress'
  | 'highlight_text'
  | 'typewriter'
  | 'progress_steps'
  | 'notification'
  | 'background_pattern'
  | 'lower_third';
export type ComponentVariant = 'default' | 'primary' | 'success' | 'danger' | 'warning' | 'muted';
export type IconName =
  | 'sparkles'
  | 'brain'
  | 'workflow'
  | 'image'
  | 'video'
  | 'audio'
  | 'check'
  | 'x'
  | 'zap'
  | 'target'
  | 'layers'
  | 'code'
  | 'settings';
export type ComponentSlot =
  | 'title'
  | 'left_top'
  | 'left_bottom'
  | 'right_top'
  | 'right_bottom'
  | 'center'
  | 'bottom'
  | 'caption';
export type MotionType = 'fade_in' | 'slide_in' | 'pop' | 'draw' | 'strike' | 'pulse' | 'none';

export interface ComponentSpec {
  id: string;
  type: ComponentType;
  slot: ComponentSlot;
  text?: string;
  variant?: ComponentVariant;
  motion?: MotionType;
  icon?: IconName;
}

export interface RemotionSceneSpec {
  scene_index: number;
  duration: number;
  template: 'basic_diagram';
  theme: 'warm_grid' | 'dark_grid' | 'clean';
  headline: string;
  subtitle?: string;
  components: ComponentSpec[];
}

export interface RemotionVideoSpec {
  title: string;
  width: number;
  height: number;
  fps: number;
  scenes: RemotionSceneSpec[];
}
