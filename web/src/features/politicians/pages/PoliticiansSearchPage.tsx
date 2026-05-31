import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { apiClient } from '../../../shared/api/client';
import { Politician } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { MultiSelectDropdown } from '../../../shared/ui/MultiSelectDropdown';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

type Filters = {
  query: string;
  cargo: string[];
  partido: string[];
  uf: string[];
  cidade: string[];
  status_politico: string[];
  identidade_tipo: 'atual' | 'historica' | 'todas';
};

const initialFilters: Filters = {
  query: '',
  cargo: [],
  partido: [],
  uf: [],
  cidade: [],
  status_politico: [],
  identidade_tipo: 'atual',
};

function getPoliticianStatusStyle(status: string) {
  const normalized = status.trim().toLowerCase();
  if (normalized === 'ativo') {
    return { color: '#14532D', fontWeight: 700 };
  }
  if (normalized === 'cassado') {
    return { color: '#B91C1C', fontWeight: 700 };
  }
  if (normalized === 'desligado') {
    return { color: '#111111', fontWeight: 700 };
  }
  return { color: '#5C6B7A', fontWeight: 700 };
}

export function PoliticiansSearchPage() {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [allPoliticians, setAllPoliticians] = useState<Politician[]>([]);
  const [politicians, setPoliticians] = useState<Politician[]>([]);
  const [hasLoadedInitialData, setHasLoadedInitialData] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const requestSequenceRef = useRef(0);

  useEffect(() => {
    setIsLoading(true);
    apiClient.getPoliticians<Politician[]>()
      .then((data) => {
        setAllPoliticians(data);
        setPoliticians(data);
        setHasLoadedInitialData(true);
      })
      .catch(() => {
        setAllPoliticians([]);
        setPoliticians([]);
        setHasLoadedInitialData(true);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!hasLoadedInitialData) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      const requestId = requestSequenceRef.current + 1;
      requestSequenceRef.current = requestId;
      setIsLoading(true);

      apiClient.getPoliticians<Politician[]>(filters)
        .then((data) => {
          if (requestSequenceRef.current !== requestId) {
            return;
          }
          setPoliticians(data);
        })
        .catch(() => {
          if (requestSequenceRef.current !== requestId) {
            return;
          }
          setPoliticians([]);
        })
        .finally(() => {
          if (requestSequenceRef.current !== requestId) {
            return;
          }
          setIsLoading(false);
        });
    }, 250);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [filters, hasLoadedInitialData]);

  const options = useMemo(() => ({
    cargo: Array.from(new Set(allPoliticians.map((item) => item.cargo).filter(Boolean))).sort(),
    partido: Array.from(new Set(allPoliticians.map((item) => item.partido).filter(Boolean))).sort(),
    uf: Array.from(new Set(allPoliticians.map((item) => item.uf).filter(Boolean))).sort(),
    cidade: Array.from(
      new Set(
        allPoliticians
          .filter((item) => filters.uf.length === 0 || filters.uf.includes(item.uf))
          .map((item) => item.cidade)
          .filter((value): value is string => Boolean(value))
      )
    ).sort(),
    status_politico: ['ativo', 'desligado', 'cassado'],
  }), [allPoliticians, filters.uf]);

  const identityOptions = useMemo(() => ([
    { value: 'atual', label: t('politicians.identityCurrent') },
    { value: 'historica', label: t('politicians.identityHistorical') },
    { value: 'todas', label: t('politicians.identityAll') },
  ]), [t]);

  const handleChange = (field: keyof Filters) => (event: ChangeEvent<HTMLInputElement>) => {
    setFilters((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleMultiChange = (field: Exclude<keyof Filters, 'query'>) => (values: string[]) => {
    setFilters((current) => {
      if (field !== 'uf') {
        return { ...current, [field]: values };
      }

      const allowedCities = new Set(
        allPoliticians
          .filter((item) => values.length === 0 || values.includes(item.uf))
          .map((item) => item.cidade)
          .filter((value): value is string => Boolean(value))
      );

      return {
        ...current,
        uf: values,
        cidade: current.cidade.filter((city) => allowedCities.has(city)),
      };
    });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const requestId = requestSequenceRef.current + 1;
    requestSequenceRef.current = requestId;
    setIsLoading(true);

    try {
      const data = await apiClient.getPoliticians<Politician[]>(filters);
      if (requestSequenceRef.current === requestId) {
        setPoliticians(data);
      }
    } catch {
      if (requestSequenceRef.current === requestId) {
        setPoliticians([]);
      }
    } finally {
      if (requestSequenceRef.current === requestId) {
        setIsLoading(false);
      }
    }
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="politicians-page">
      <Card>
        <SectionTitle
          title={t('politicians.title')}
          subtitle={t('politicians.subtitle')}
          action={<InfoHint title={t('education.rolesTitle')} body={t('education.rolesBody')} />}
        />
        {isLoading ? <p style={{ margin: '0 0 16px', color: '#5C6B7A' }} data-testid="politicians-loading">Buscando parlamentares...</p> : null}
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }} data-testid="politicians-search-form">
          <label style={{ display: 'grid', gap: '8px' }}>
            <span>{t('politicians.nameLabel')}</span>
            <input data-testid="politicians-search-input" value={filters.query} onChange={handleChange('query')} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px' }} />
          </label>
          <label style={{ display: 'grid', gap: '8px' }}>
            <span>{t('politicians.identityLabel')}</span>
            <select value={filters.identidade_tipo} onChange={(event) => setFilters((current) => ({ ...current, identidade_tipo: event.target.value as Filters['identidade_tipo'] }))} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
              {identityOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <MultiSelectDropdown label={t('politicians.roleLabel')} options={options.cargo} selectedValues={filters.cargo} onChange={handleMultiChange('cargo')} />
          <MultiSelectDropdown label={t('politicians.partyLabel')} options={options.partido} selectedValues={filters.partido} onChange={handleMultiChange('partido')} />
          <MultiSelectDropdown label={t('politicians.stateLabel')} options={options.uf} selectedValues={filters.uf} onChange={handleMultiChange('uf')} />
          <MultiSelectDropdown label={t('politicians.cityLabel')} options={options.cidade} selectedValues={filters.cidade} onChange={handleMultiChange('cidade')} disabled={filters.uf.length === 0} />
          <MultiSelectDropdown label={t('politicians.statusLabel')} options={options.status_politico} selectedValues={filters.status_politico} onChange={handleMultiChange('status_politico')} />
          <div style={{ display: 'flex', alignItems: 'end' }}>
            <button type="submit" style={{ minHeight: '44px', borderRadius: '999px', border: 'none', background: '#0F4C81', color: '#FFFFFF', padding: '0 18px' }} data-testid="politicians-search-submit">
              {t('politicians.searchCta')}
            </button>
          </div>
        </form>
      </Card>

      {politicians.length === 0 ? (
        <Card>
          <p style={{ margin: 0 }}>{t('politicians.empty')}</p>
        </Card>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }} data-testid="politicians-results">
          {politicians.map((politician) => (
            <Card key={politician.id}>
              <div data-testid="politician-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px' }}>{politician.nome}</h3>
                  <p style={{ margin: '0 0 6px', color: '#5C6B7A' }}>{politician.cargo} · {politician.partido}/{politician.uf}</p>
                  <p style={{ margin: 0, color: '#5C6B7A' }}>{politician.cidade ?? 'Cidade não informada'}</p>
                  <p style={{ margin: '6px 0 0', ...getPoliticianStatusStyle(politician.status_politico) }}>{politician.status_politico}</p>
                  {politician.identidade_tipo === 'historica' ? <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>Registro histórico{politician.legislatura ? ` · legislatura ${politician.legislatura}` : ''}</p> : null}
                </div>
                <Link to={`/politicos/${politician.id}`} style={{ minHeight: '44px', display: 'inline-flex', alignItems: 'center' }} data-testid="politician-open-history">
                  {t('politicians.openHistory')}
                </Link>
              </div>
            </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
