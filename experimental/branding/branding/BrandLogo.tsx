import React, { useEffect, useState } from 'react';

// Lightweight React wrapper around the SVG logo for easy import
export const BrandLogo: React.FC<{ size?: number }>=({ size = 40 }) => {
  const [variant, setVariant] = useState<string>(typeof window !== 'undefined' ? (localStorage.getItem('branding_logo_variant') ?? 'default') : 'default');

  useEffect(() => {
    const listener = () => {
      const v = localStorage.getItem('branding_logo_variant') ?? 'default';
      if (v !== variant) setVariant(v);
    };
    window.addEventListener('branding-variant-changed', listener);
    return () => window.removeEventListener('branding-variant-changed', listener);
  }, [variant]);

  const src = variant === 'alt' ? './assets/logo-alt.svg' : './assets/logo.svg';
  // Note: Using relative path for bundler; Webpack/Vite will resolve
  return (
    <img
      src={new URL(src, import.meta.url).toString()}
      alt="Infra Pilot logo"
      style={{ width: size, height: size, display: 'block' }}
    />
  );
};

export default BrandLogo;
