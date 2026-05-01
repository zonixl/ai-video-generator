import React from 'react';
import {ArrowRight, MoveRight} from 'lucide-react';

export const Arrow: React.FC<{progress: number; style?: React.CSSProperties; label?: string}> = ({progress, style, label}) => {
  const clamped = Math.max(0, Math.min(1, progress));
  const width = clamped * 142;
  return (
    <div style={{position: 'relative', width: 178, height: 86, color: '#334155', ...style}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: 999,
          background: 'rgba(255,255,255,0.64)',
          border: '1.5px solid rgba(51,65,85,0.12)',
          boxShadow: '0 14px 38px rgba(28,35,58,0.10)',
          backdropFilter: 'blur(14px)',
          opacity: 0.9
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 18,
          top: 38,
          width,
          height: 4,
          borderRadius: 999,
          background: 'linear-gradient(90deg, rgba(51,65,85,0.24), #334155)'
        }}
      />
      <div
        style={{
          position: 'absolute',
          right: 14,
          top: 24,
          opacity: clamped,
          transform: `translateX(${(1 - clamped) * -18}px)`
        }}
      >
        <ArrowRight size={38} strokeWidth={2.3} />
      </div>
      {label ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: -34,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            fontSize: 22,
            fontWeight: 800,
            color: '#64748b'
          }}
        >
          <MoveRight size={20} strokeWidth={2.2} />
          {label}
        </div>
      ) : null}
    </div>
  );
};
