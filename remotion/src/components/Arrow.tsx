import React from 'react';

export const Arrow: React.FC<{progress: number; style?: React.CSSProperties}> = ({progress, style}) => {
  const width = Math.max(0, Math.min(1, progress)) * 140;
  return (
    <div style={{position: 'relative', width: 170, height: 70, ...style}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 30,
          width,
          height: 12,
          borderRadius: 999,
          background: '#202124'
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: Math.max(0, width - 30),
          top: 15,
          width: 36,
          height: 36,
          borderRight: '12px solid #202124',
          borderTop: '12px solid #202124',
          transform: 'rotate(45deg)',
          opacity: progress > 0.82 ? 1 : 0
        }}
      />
    </div>
  );
};
