import { useState } from 'react';

type InfoHintProps = {
  label?: string;
  title: string;
  body: string;
};

export function InfoHint({ label = '?', title, body }: InfoHintProps) {
  const [open, setOpen] = useState(false);

  return (
    <span
      style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={title}
        onClick={() => setOpen((current) => !current)}
        style={{
          width: '24px',
          height: '24px',
          borderRadius: '999px',
          border: '1px solid #9DB6CC',
          background: '#EFF6FF',
          color: '#0F4C81',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 0,
          lineHeight: 1,
        }}
      >
        {label}
      </button>
      {open ? (
        <span
          role="tooltip"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 'min(320px, calc(100vw - 32px))',
            minWidth: '220px',
            maxWidth: 'calc(100vw - 32px)',
            background: '#FFFFFF',
            border: '1px solid #D7DEE5',
            borderRadius: '16px',
            boxShadow: '0 12px 30px rgba(15, 76, 129, 0.16)',
            padding: '12px 14px',
            zIndex: 20,
            color: '#16202A',
          }}
        >
          <strong style={{ display: 'block', marginBottom: '6px', fontSize: '0.95rem' }}>{title}</strong>
          <span style={{ color: '#5C6B7A', fontSize: '0.95rem', lineHeight: 1.45 }}>{body}</span>
        </span>
      ) : null}
    </span>
  );
}
