import React from 'react';
import './LiquidGlass.css';

type GlassEffectContainerProps = {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
};

export const GlassEffectContainer: React.FC<GlassEffectContainerProps> = ({
  children,
  style,
  className = '',
}) => {
  return (
    <div
      className={`lg-glass-morph ${className}`}
      style={{
        position: 'relative',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default GlassEffectContainer;
