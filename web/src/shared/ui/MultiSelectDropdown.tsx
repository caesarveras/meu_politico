import { KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';

type MultiSelectDropdownProps = {
  label: string;
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
};

export function MultiSelectDropdown({ label, options, selectedValues, onChange, disabled = false }: MultiSelectDropdownProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [query, open, options, selectedValues]);

  const filteredOptions = useMemo(() => {
    if (disabled) {
      return [];
    }
    const normalizedQuery = query.trim().toLowerCase();
    return options.filter((option) => option.toLowerCase().includes(normalizedQuery) && !selectedValues.includes(option));
  }, [disabled, options, query, selectedValues]);

  const addValue = (value: string) => {
    onChange([...selectedValues, value]);
    setQuery('');
    setOpen(false);
  };

  const removeValue = (value: string) => {
    onChange(selectedValues.filter((item) => item !== value));
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (disabled) {
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setHighlightedIndex((current) => Math.min(current + 1, Math.max(filteredOptions.length - 1, 0)));
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setOpen(true);
      setHighlightedIndex((current) => Math.max(current - 1, 0));
      return;
    }

    if (event.key === 'Enter' && open && filteredOptions.length > 0) {
      event.preventDefault();
      addValue(filteredOptions[highlightedIndex] ?? filteredOptions[0]);
      return;
    }

    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} style={{ display: 'grid', gap: '8px', position: 'relative' }}>
      <span>{label}</span>
      <div style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '8px 12px', background: '#FFFFFF' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: selectedValues.length > 0 ? '8px' : 0 }}>
          {selectedValues.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => removeValue(value)}
              style={{ border: '1px solid #0F4C81', background: '#EFF6FF', color: '#0F4C81', borderRadius: '999px', padding: '4px 10px', cursor: 'pointer' }}
            >
              {value} ×
            </button>
          ))}
        </div>
        <input
          value={query}
          disabled={disabled}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => !disabled && setOpen(true)}
          onClick={() => !disabled && setOpen(true)}
          placeholder={disabled ? 'Selecione primeiro uma UF' : 'Digite para pesquisar e selecionar'}
          style={{ width: '100%', border: 'none', outline: 'none', minHeight: '24px', background: 'transparent', color: disabled ? '#94A3B8' : '#16202A', cursor: disabled ? 'not-allowed' : 'text' }}
        />
      </div>
      {open ? (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10, background: '#FFFFFF', border: '1px solid #D7DEE5', borderRadius: '12px', boxShadow: '0 8px 24px rgba(15, 76, 129, 0.12)', overflowY: 'auto', overflowX: 'hidden', maxHeight: '240px' }}>
          {filteredOptions.length > 0 ? (
            filteredOptions.map((option, index) => (
              <button
                key={option}
                type="button"
                onClick={() => addValue(option)}
                onMouseEnter={() => setHighlightedIndex(index)}
                style={{ width: '100%', textAlign: 'left', padding: '12px', border: 'none', background: highlightedIndex === index ? '#EFF6FF' : '#FFFFFF', color: highlightedIndex === index ? '#0F4C81' : '#16202A', cursor: 'pointer' }}
              >
                {option}
              </button>
            ))
          ) : (
            <div style={{ padding: '12px', color: '#5C6B7A' }}>Nenhuma opção encontrada</div>
          )}
        </div>
      ) : null}
    </div>
  );
}
