import type { ReactNode } from 'react';

type PageHeaderProps = {
  eyebrow: string;
  children: ReactNode;
  actions?: ReactNode;
};

export const PageHeader = ({ eyebrow, children, actions }: PageHeaderProps) => (
  <>
    <div className="flex items-start justify-between">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        {children}
      </div>
      {actions}
    </div>
    <div className="page-rule" />
  </>
);
