import React from 'react';
import {useCurrentFrame} from 'remotion';
import {ArrowRight, MoveRight} from 'lucide-react';

const DOT_COUNT = 5;

export const Arrow: React.FC<{progress: number; style?: React.CSSProperties; label?: string}> = ({
  progress,
  style,
  label,
}) => {
  const frame = useCurrentFrame();
  const clamped = Math.max(0, Math.min(1, progress));
  const lineWidth = clamped * 120;

  // tip pulse glow
  const glow = 1 + Math.sin(frame / 14) * 0.28;

  return (
    <div style={{position: 'relative', width: 178, height: 86, color: '#334155', ...style}}>
      {/* flowing dot trail */}
      {Array.from({length: DOT_COUNT}).map((_, i) => {
        const dotProgress = ((frame * 1.6 + i * (120 / DOT_COUNT)) % 120) / 120;
        if (dotProgress > clamped) return null;
        const dotX = 28 + dotProgress * 120;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: dotX,
              top: 38,
              width: 5,
              height: 5,
              borderRadius: 999,
              background: '#0ea5e9',
              opacity: 0.5 + Math.sin(frame / 7 + i) * 0.3,
              boxShadow: '0 0 6px rgba(14,165,233,0.45)',
            }}
          />
        );
      })}

      {/* progress line */}
      <div
        style={{
          position: 'absolute',
          left: 28,
          top: 40,
          width: lineWidth,
          height: 3,
          borderRadius: 999,
          background: 'linear-gradient(90deg, rgba(14,165,233,0.3), #0ea5e9)',
          transition: 'width 0.15s linear',
        }}
      />

      {/* arrow tip with glow */}
      <div
        style={{
          position: 'absolute',
          right: 24,
          top: 22,
          opacity: clamped,
          transform: `scale(${glow})`,
          filter: `drop-shadow(0 0 ${5 * glow}px rgba(14,165,233,0.5))`,
        }}
      >
        <ArrowRight size={36} strokeWidth={2.4} color="#0ea5e9" />
      </div>

      {label ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: -8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            fontSize: 22,
            fontWeight: 800,
            color: '#64748b',
          }}
        >
          <MoveRight size={20} strokeWidth={2.2} />
          {label}
        </div>
      ) : null}
    </div>
  );
};
