import React from 'react';

type Props = {
  title: string;
  children?: React.ReactNode;
};

export const BrandCard: React.FC<Props> = ({ title, children }) => {
  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-2 text-white">{title}</h3>
      <div className="text-sm text-white/60">{children}</div>
    </div>
  );
};

export default BrandCard;
