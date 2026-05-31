import { PropsWithChildren } from 'react';

export function Card({ children }: PropsWithChildren) {
  return (
    <section
      style={{
        background: '#FFFFFF',
        border: '1px solid #D7DEE5',
        borderRadius: '20px',
        padding: '20px',
        boxShadow: '0 4px 16px rgba(15, 76, 129, 0.06)',
      }}
    >
      {children}
    </section>
  );
}
