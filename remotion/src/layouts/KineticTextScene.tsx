import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {RemotionSceneSpec, LineAnim, WordAnim, KineticConfig} from '../schema';
import {Canvas} from '../components/Canvas';

/** 单个词的动画渲染 */
const AnimatedWord: React.FC<{
  word: WordAnim;
  lineStart: number;
  fps: number;
  frame: number;
}> = ({word, lineStart, fps, frame}) => {
  const wordStartFrame = lineStart + word.start * fps;
  const wordFrame = frame - wordStartFrame;

  if (wordFrame < -fps * 0.3) return null;

  // 入场弹簧动画 — 更弹、更有冲击力
  const enter = spring({
    frame: wordFrame,
    fps,
    config: {damping: 8, stiffness: 200, mass: 0.5},
  });

  // scale: 从 word.scale 弹回 1.0（更大的弹性范围）
  const currentScale = 1 + (word.scale - 1) * Math.max(0, 1 - enter);

  // translateY: 从 word.dy 上浮到 0
  const currentDy = word.dy * Math.max(0, 1 - enter);

  // 入场时的 opacity — 快速出现
  const opacity = Math.min(1, enter * 2.5);

  // 入场时轻微旋转增加活力
  const rotation = (1 - enter) * (word.scale > 1.8 ? -8 : 4);

  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: word.font_size || 72,
        fontWeight: 900,
        color: word.color || '#ffffff',
        opacity,
        transform: `scale(${currentScale}) translateY(${currentDy}px) rotate(${rotation}deg)`,
        textShadow: word.scale >= 1.8
          ? `0 0 ${20 * enter}px ${word.color}44, 0 4px 24px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3)`
          : '0 4px 24px rgba(0,0,0,0.45), 0 2px 8px rgba(0,0,0,0.3)',
        letterSpacing: '0.02em',
        margin: '0 8px',
        willChange: 'transform, opacity',
      }}
    >
      {word.text}
    </span>
  );
};

/** 单行动画渲染 + 翻转退出 + 向上漂移 */
const AnimatedLine: React.FC<{
  line: LineAnim;
  nextLineStart: number | null;
  fps: number;
  frame: number;
  globalStyle: KineticConfig['global_style'];
}> = ({line, nextLineStart, fps, frame, globalStyle}) => {
  const lineStartFrame = line.start * fps;

  // 行翻转退出动画 — 更长、更戏剧化
  let exitTransform = '';
  let exitOpacity = 1;

  if (nextLineStart !== null) {
    const exitStartFrame = nextLineStart * fps;
    if (frame >= exitStartFrame) {
      // 翻转：沿 X 轴旋转 90 度，持续 15 帧
      const flipProgress = interpolate(
        frame,
        [exitStartFrame, exitStartFrame + 15],
        [0, 90],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
      );
      // 翻转同时向上漂移
      const exitDrift = interpolate(
        frame,
        [exitStartFrame, exitStartFrame + 15],
        [0, -60],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
      );
      exitOpacity = interpolate(
        frame,
        [exitStartFrame, exitStartFrame + 12],
        [1, 0],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
      );
      exitTransform = `perspective(${globalStyle.perspective}px) rotateX(${flipProgress}deg) translateY(${exitDrift}px)`;
    }
  }

  // 行入场 — 从下方滑入，更有弹性
  const lineEnter = spring({
    frame: frame - lineStartFrame,
    fps,
    config: {damping: 10, stiffness: 160, mass: 0.7},
  });
  const lineTranslateY = (1 - lineEnter) * 50;

  return (
    <div
      style={{
        position: 'absolute',
        top: `${line.y_position}%`,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: globalStyle.text_align === 'left' ? 'flex-start' : 'center',
        alignItems: 'center',
        flexWrap: 'wrap',
        padding: '0 60px',
        transform: `translateY(${lineTranslateY}px) ${exitTransform}`,
        opacity: exitOpacity * Math.min(1, lineEnter * 1.5),
        willChange: 'transform, opacity',
      }}
    >
      {line.words.map((word, wIdx) => (
        <AnimatedWord
          key={`${line.line_index}-${wIdx}`}
          word={word}
          lineStart={line.start}
          fps={fps}
          frame={frame}
        />
      ))}
    </div>
  );
};

/** 逐词动态文字场景 */
export const KineticTextScene: React.FC<{scene: RemotionSceneSpec}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const config = scene.kinetic_config as KineticConfig | undefined;

  if (!config || !config.lines || config.lines.length === 0) {
    // fallback: 显示字幕，加大字号
    return (
      <Canvas scene={scene}>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: 72,
            fontWeight: 900,
            color: '#ffffff',
            textAlign: 'center',
            textShadow: '0 4px 24px rgba(0,0,0,0.45)',
            padding: '0 60px',
            lineHeight: 1.4,
          }}
        >
          {scene.subtitle || scene.headline}
        </div>
      </Canvas>
    );
  }

  const globalStyle = config.global_style || {text_align: 'center', perspective: 800};

  // 按 start 排序行
  const sortedLines = [...config.lines].sort((a, b) => a.start - b.start);

  // 找到当前活跃行索引（start 已过 且 还没被下一行完全替代）
  const FLIP_DURATION_FRAMES = 15;
  let activeIdx = 0;
  for (let i = sortedLines.length - 1; i >= 0; i--) {
    if (frame >= sortedLines[i].start * fps) {
      activeIdx = i;
      break;
    }
  }

  // 只渲染当前行 + 最多 2 行历史（正在翻转退出的），总计不超过 3 行
  const visibleStart = Math.max(0, activeIdx - 2);
  const visibleLines = sortedLines.slice(visibleStart);

  return (
    <Canvas scene={scene}>
      {visibleLines.map((line) => {
        const origIdx = sortedLines.indexOf(line);
        const nextLine = sortedLines[origIdx + 1];
        const nextLineStart = nextLine ? nextLine.start : null;

        return (
          <AnimatedLine
            key={line.line_index}
            line={line}
            nextLineStart={nextLineStart}
            fps={fps}
            frame={frame}
            globalStyle={globalStyle}
          />
        );
      })}
    </Canvas>
  );
};
