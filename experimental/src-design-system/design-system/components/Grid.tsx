import React from 'react';
import { useTheme } from '../theme/ThemeProvider';

type GridProps = {
  columns?: number;
  gap?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

export const Grid: React.FC<GridProps> = ({ columns = 3, gap = 12, children, style }) => {
  const theme = useTheme() as any;
  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: gap ?? 12,
    alignItems: 'stretch',
    width: '100%',
    ...style,
  };
  return <div style={gridStyle}>{children}</div>;
};

export default Grid;
