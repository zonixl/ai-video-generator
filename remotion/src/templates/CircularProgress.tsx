import React from 'react';
import type {ComponentSpec} from '../schema';
import {DonutChart} from './DonutChart';

export const CircularProgress: React.FC<{component: ComponentSpec; style?: React.CSSProperties}> = ({component, style}) => (
  <DonutChart component={component} style={style} />
);
