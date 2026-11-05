import React from 'react';

type Props = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export const BrandInput: React.FC<Props> = ({ label, ...rest }) => {
  return (
    <div>
      {label && <label className="mb-1 block text-sm font-medium text-white/55">{label}</label>}
      <input className="input-field w-full text-sm" {...rest} />
    </div>
  );
};

export default BrandInput;
