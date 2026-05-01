import React from 'react';
import type {ComponentSpec} from '../schema';

export const TextBlock: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => (
  <div
    style={{
      fontSize: 42,
      fontWeight: 900,
      lineHeight: 1.25,
      textAlign: 'center',
      ...style
    }}
  >
    {component.text}
  </div>
);
