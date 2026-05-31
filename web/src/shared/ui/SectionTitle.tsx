import { ReactNode } from 'react';

type SectionTitleProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
};

export function SectionTitle({ title, subtitle, action }: SectionTitleProps) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: '1.5rem' }}>{title}</h2>
        {action}
      </div>
      {subtitle ? <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>{subtitle}</p> : null}
    </div>
  );
}
