import React from 'react';
import {useCurrentFrame, spring} from 'remotion';
import {ArrowRight, ArrowDown, MoveRight} from 'lucide-react';

export const Arrow: React.FC<{
  progress: number;
  style?: React.CSSProperties;
  label?: string;
  direction?: 'right' | 'down';
}> = ({progress, style, label, direction = 'right'}) => {
  const frame = useCurrentFrame();
  const clamped = Math.max(0, Math.min(1, progress));

  // subtle pulse
  const pulse = 1 + Math.sin(frame / 14) * 0.15;

  // entrance spring
  const enter = spring({
    frame: frame - 4,
    fps: 30,
    config: {damping: 14, stiffness: 160, mass: 0.7},
  });

  const ArrowIcon = direction === 'down' ? ArrowDown : ArrowRight;
  const containerStyle: React.CSSProperties = direction === 'right'
    ? {width: 178, height: 86}
    : {width: 178, height: 86, transform: 'rotate(90deg)'};

  return (
    <div style={{
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      ...containerStyle,
      color: '#334155',
      opacity: enter,
      transform: `${containerStyle.transform || ''} scale(${0.85 + enter * 0.15})`,
      ...style,
    }}>
      {/* arrow tip icon only — clean, no line extending into cards */}
      <div
        style={{
          opacity: clamped,
          transform: `scale(${pulse})`,
          filter: `drop-shadow(0 0 ${5 * pulse}px rgba(14,165,233,0.5))`,
        }}
      >
        <ArrowIcon size={42} strokeWidth={2.2} color="#0ea5e9" />
      </div>

      {label ? (
        <div
          style={{
            marginTop: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 22,
            fontWeight: 800,
            color: '#64748b',
          }}
        >
          <MoveRight size={18} strokeWidth={2} />
          {label}
        </div>
      ) : null}
    </div>
  );
};
