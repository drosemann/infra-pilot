import React from 'react';

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
};

export const BrandButton: React.FC<Props> = ({ label, ...rest }) => {
  return (
    <button
      className="primary-button disabled:opacity-50"
      {...rest}
    >
      {label}
    </button>
  );
};

export default BrandButton;
