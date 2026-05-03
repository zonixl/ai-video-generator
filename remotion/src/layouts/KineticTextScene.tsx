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
  globalPerspective: number;
}> = ({word, lineStart, fps, frame, globalPerspective}) => {
  const wordStartFrame = lineStart + word.start * fps;
  const wordFrame = frame - wordStartFrame;

  if (wordFrame < -fps * 0.5) return null; // 还没到出现时间

  // 入场弹簧动画
  const enter = spring({
    frame: wordFrame,
    fps,
    config: {damping: 12, stiffness: 180, mass: 0.7},
  });

  // scale: 从 word.scale 弹回 1.0
  const currentScale = 1 + (word.scale - 1) * Math.max(0, 1 - enter);

  // translateY: 从 word.dy 上浮到 0
  const currentDy = word.dy * Math.max(0, 1 - enter);

  // 入场时的 opacity
  const opacity = Math.min(1, enter * 2);

  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: word.font_size || 56,
        fontWeight: 900,
        color: word.color || '#ffffff',
        opacity,
        transform: `scale(${currentScale}) translateY(${currentDy}px)`,
        textShadow: '0 4px 24px rgba(0,0,0,0.45), 0 2px 8px rgba(0,0,0,0.3)',
        letterSpacing: '0.02em',
        margin: '0 6px',
        willChange: 'transform, opacity',
      }}
    >
      {word.text}
    </span>
  );
};

/** 单行动画渲染 + 翻转退出 */
const AnimatedLine: React.FC<{
  line: LineAnim;
  nextLineStart: number | null;
  fps: number;
  frame: number;
  globalStyle: KineticConfig['global_style'];
}> = ({line, nextLineStart, fps, frame, globalStyle}) => {
  const lineStartFrame = line.start * fps;

  // 行翻转退出动画
  let exitTransform = '';
  let exitOpacity = 1;

  if (nextLineStart !== null) {
    const exitStartFrame = nextLineStart * fps;
    if (frame >= exitStartFrame) {
      // 翻转：沿 X 轴旋转 90 度
      const flipProgress = interpolate(
        frame,
        [exitStartFrame, exitStartFrame + 10],
        [0, 90],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
      );
      exitOpacity = interpolate(
        frame,
        [exitStartFrame, exitStartFrame + 8],
        [1, 0],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
      );
      exitTransform = `perspective(${globalStyle.perspective}px) rotateX(${flipProgress}deg)`;
    }
  }

  // 行入场（从下方滑入）
  const lineEnter = spring({
    frame: frame - lineStartFrame,
    fps,
    config: {damping: 16, stiffness: 140, mass: 0.9},
  });
  const lineTranslateY = (1 - lineEnter) * 30;

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
        padding: '0 80px',
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
          globalPerspective={globalStyle.perspective}
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
    // fallback: 显示字幕
    return (
      <Canvas scene={scene}>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: 56,
            fontWeight: 900,
            color: '#ffffff',
            textAlign: 'center',
            textShadow: '0 4px 24px rgba(0,0,0,0.45)',
            padding: '0 80px',
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

  return (
    <Canvas scene={scene}>
      {sortedLines.map((line, idx) => {
        const nextLine = sortedLines[idx + 1];
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
