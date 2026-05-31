import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { apiClient } from '../../../shared/api/client';
import { ApprovedBillFacets, ApprovedBillsSearchResponse, Bill } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

const PAGE_SIZE = 12;

export function BillsApprovedPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [themeQuery, setThemeQuery] = useState(() => searchParams.get('tema') ?? '');
  const [selectedAuthor, setSelectedAuthor] = useState(() => searchParams.get('autor') ?? '');
  const [selectedParty, setSelectedParty] = useState(() => searchParams.get('partido') ?? '');
  const [selectedYearFrom, setSelectedYearFrom] = useState(() => searchParams.get('ano_de') ?? '');
  const [selectedYearTo, setSelectedYearTo] = useState(() => searchParams.get('ano_ate') ?? '');
  const [currentPage, setCurrentPage] = useState(() => {
    const page = Number(searchParams.get('pagina') ?? '1');
    return Number.isFinite(page) && page > 0 ? page : 1;
  });
  const [bills, setBills] = useState<Bill[]>([]);
  const [facets, setFacets] = useState<ApprovedBillFacets>({ authors: [], parties: [], years: [] });
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    apiClient.getApprovedBillFacets<ApprovedBillFacets>().then((data) => setFacets(data)).catch(() => setFacets({ authors: [], parties: [], years: [] }));
  }, []);

  const authorOptions = useMemo(() => facets.authors, [facets.authors]);
  const partyOptions = useMemo(() => facets.parties, [facets.parties]);
  const yearOptions = useMemo(() => facets.years.map(String), [facets.years]);

  useEffect(() => {
    if (!selectedYearFrom || !selectedYearTo) {
      return;
    }

    if (Number(selectedYearFrom) > Number(selectedYearTo)) {
      setSelectedYearTo(selectedYearFrom);
    }
  }, [selectedYearFrom, selectedYearTo]);

  useEffect(() => {
    setIsLoading(true);
    apiClient.searchApprovedBills<ApprovedBillsSearchResponse>({
      theme: themeQuery.trim() || undefined,
      author: selectedAuthor || undefined,
      party: selectedParty || undefined,
      year_from: selectedYearFrom ? Number(selectedYearFrom) : undefined,
      year_to: selectedYearTo ? Number(selectedYearTo) : undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    }).then((response) => {
      setBills(response.data);
      setTotalCount(response.meta.total_count);
      setTotalPages(response.meta.total_pages);
      if (response.meta.total_pages > 0 && currentPage > response.meta.total_pages) {
        setCurrentPage(response.meta.total_pages);
      }
    }).catch(() => {
      setBills([]);
      setTotalCount(0);
      setTotalPages(0);
    }).finally(() => {
      setIsLoading(false);
    });
  }, [currentPage, selectedAuthor, selectedParty, selectedYearFrom, selectedYearTo, themeQuery]);

  useEffect(() => {
    const nextParams = new URLSearchParams();

    if (themeQuery.trim()) {
      nextParams.set('tema', themeQuery.trim());
    }
    if (selectedAuthor) {
      nextParams.set('autor', selectedAuthor);
    }
    if (selectedParty) {
      nextParams.set('partido', selectedParty);
    }
    if (selectedYearFrom) {
      nextParams.set('ano_de', selectedYearFrom);
    }
    if (selectedYearTo) {
      nextParams.set('ano_ate', selectedYearTo);
    }
    if (currentPage > 1) {
      nextParams.set('pagina', String(currentPage));
    }

    setSearchParams(nextParams, { replace: true });
  }, [currentPage, selectedAuthor, selectedParty, selectedYearFrom, selectedYearTo, setSearchParams, themeQuery]);

  const activeFilters = useMemo(() => {
    const items: Array<{ key: string; label: string; onRemove: () => void }> = [];
    if (themeQuery.trim()) items.push({ key: 'tema', label: `${t('bills.themeLabel')}: ${themeQuery.trim()}`, onRemove: () => { setThemeQuery(''); setCurrentPage(1); } });
    if (selectedAuthor) items.push({ key: 'autor', label: `${t('bills.authorLabel')}: ${selectedAuthor}`, onRemove: () => { setSelectedAuthor(''); setCurrentPage(1); } });
    if (selectedParty) items.push({ key: 'partido', label: `${t('bills.partyLabel')}: ${selectedParty}`, onRemove: () => { setSelectedParty(''); setCurrentPage(1); } });
    if (selectedYearFrom) items.push({ key: 'ano_de', label: `${t('bills.yearFromLabel')}: ${selectedYearFrom}`, onRemove: () => { setSelectedYearFrom(''); setCurrentPage(1); } });
    if (selectedYearTo) items.push({ key: 'ano_ate', label: `${t('bills.yearToLabel')}: ${selectedYearTo}`, onRemove: () => { setSelectedYearTo(''); setCurrentPage(1); } });
    return items;
  }, [selectedAuthor, selectedParty, selectedYearFrom, selectedYearTo, t, themeQuery]);

  const paginationItems = useMemo(() => {
    if (totalPages <= 1) {
      return [] as Array<number | string>;
    }

    const pages = new Set<number>([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
    const normalizedPages = Array.from(pages)
      .filter((page) => page >= 1 && page <= totalPages)
      .sort((left, right) => left - right);

    const items: Array<number | string> = [];
    normalizedPages.forEach((page, index) => {
      const previousPage = normalizedPages[index - 1];
      if (previousPage && page - previousPage > 1) {
        items.push(`ellipsis-${previousPage}-${page}`);
      }
      items.push(page);
    });

    return items;
  }, [currentPage, totalPages]);

  const currentRangeStart = totalCount === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const currentRangeEnd = totalCount === 0 ? 0 : currentRangeStart + bills.length - 1;

  const handleResetFilters = () => {
    setThemeQuery('');
    setSelectedAuthor('');
    setSelectedParty('');
    setSelectedYearFrom('');
    setSelectedYearTo('');
    setCurrentPage(1);
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="approved-bills-page">
      <Card>
        <SectionTitle
         title={t('bills.title')}
         action={<InfoHint title={t('education.billStatusTitle')} body={t('education.billStatusBody')} />}
       />
        <div style={{ display: 'grid', gap: '12px' }} data-testid="approved-bills-search-form">
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.themeLabel')}</span>
              <input
                data-testid="approved-bills-theme-input"
                value={themeQuery}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  setThemeQuery(event.target.value);
                  setCurrentPage(1);
                }}
                disabled={isLoading}
                placeholder={t('bills.themePlaceholder')}
                style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px' }}
              />
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.authorLabel')}</span>
              <select data-testid="approved-bills-author-select" value={selectedAuthor} onChange={(event) => { setSelectedAuthor(event.target.value); setCurrentPage(1); }} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allAuthors')}</option>
                {authorOptions.map((author) => <option key={author} value={author}>{author}</option>)}
              </select>
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.partyLabel')}</span>
              <select data-testid="approved-bills-party-select" value={selectedParty} onChange={(event) => { setSelectedParty(event.target.value); setCurrentPage(1); }} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allParties')}</option>
                {partyOptions.map((party) => <option key={party} value={party}>{party}</option>)}
              </select>
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.yearFromLabel')}</span>
              <select data-testid="approved-bills-year-from-select" value={selectedYearFrom} onChange={(event) => { setSelectedYearFrom(event.target.value); setCurrentPage(1); }} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allYears')}</option>
                {yearOptions.filter((year) => !selectedYearTo || Number(year) <= Number(selectedYearTo)).map((year) => <option key={year} value={year}>{year}</option>)}
              </select>
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.yearToLabel')}</span>
              <select data-testid="approved-bills-year-to-select" value={selectedYearTo} onChange={(event) => { setSelectedYearTo(event.target.value); setCurrentPage(1); }} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allYears')}</option>
                {yearOptions.filter((year) => !selectedYearFrom || Number(year) >= Number(selectedYearFrom)).map((year) => <option key={year} value={year}>{year}</option>)}
              </select>
            </label>
          </div>
          {isLoading ? <p style={{ margin: 0, color: '#5C6B7A' }} data-testid="approved-bills-loading">{t('bills.loading')}</p> : null}
          {activeFilters.length > 0 ? (
            <div style={{ display: 'grid', gap: '8px' }}>
              <strong>{t('bills.activeFilters')}</strong>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {activeFilters.map((filter) => (
                  <button
                    key={filter.key}
                    type="button"
                    onClick={filter.onRemove}
                    disabled={isLoading}
                    aria-label={`${t('bills.removeFilter')}: ${filter.label}`}
                    style={{ borderRadius: '999px', border: '1px solid #B7C4D1', background: '#F3F7FA', color: '#16202A', minHeight: '36px', padding: '0 12px' }}
                  >
                    {filter.label} ×
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '4px' }}>
              <span style={{ color: '#5C6B7A', fontSize: '0.95rem' }}>{totalCount} {t('bills.resultsCount')}</span>
              <span style={{ color: '#7A8896', fontSize: '0.88rem' }}>{t('bills.resultsSummary', { from: currentRangeStart, to: currentRangeEnd, total: totalCount })}</span>
            </div>
            <button type="button" onClick={handleResetFilters} disabled={isLoading || activeFilters.length === 0} style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: '#FFFFFF', color: '#0F4C81', padding: '0 18px' }} data-testid="approved-bills-clear-filters">{t('bills.clearFilters')}</button>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <div style={{ display: 'grid', gap: '16px' }} data-testid="approved-bills-skeleton-list">
          {Array.from({ length: 3 }).map((_, index) => (
            <Card key={`skeleton-${index}`}>
              <div style={{ display: 'grid', gap: '12px' }}>
                <div style={{ width: '140px', height: '16px', borderRadius: '999px', background: '#E8EEF3' }} />
                <div style={{ width: '80%', height: '24px', borderRadius: '10px', background: '#E8EEF3' }} />
                <div style={{ width: '55%', height: '16px', borderRadius: '10px', background: '#EEF3F7' }} />
              </div>
            </Card>
          ))}
        </div>
      ) : bills.length === 0 ? (
        <Card>
          <p style={{ margin: 0 }}>{activeFilters.length > 0 ? t('bills.noResults') : t('bills.empty')}</p>
        </Card>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }} data-testid="approved-bills-list">
          {bills.map((bill: Bill) => (
            <Card key={bill.id}>
              <div data-testid="approved-bill-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'start', flexWrap: 'wrap' }}>
                <div>
                  <Link to={`/leis/${bill.id}`} style={{ margin: 0, color: '#1B7F5A', fontWeight: 700, textDecoration: 'none' }}>{bill.sigla} {bill.numero}/{bill.ano}</Link>
                  <h3 style={{ marginBottom: '8px' }}><Link to={`/leis/${bill.id}`} style={{ color: '#16202A', textDecoration: 'none' }}>{bill.ementa}</Link></h3>
                  <p style={{ margin: '0 0 8px', color: '#435466' }}>{t('bills.authorLabel')}: {bill.autor_principal}</p>
                  <p style={{ margin: 0, color: '#5C6B7A' }}>{bill.status_atual}</p>
                </div>
                <div style={{ display: 'grid', gap: '8px' }}>
                  <span style={{ color: bill.aprovada ? '#1D7A46' : '#B7791F', fontWeight: 700 }}>{t('bills.approved')}</span>
                  <Link to={`/leis/${bill.id}`} style={{ color: '#0F4C81' }} data-testid="approved-bill-open-detail">{t('bills.openDetail')}</Link>
                </div>
              </div>
            </div>
            </Card>
          ))}
        </div>
      )}

      {totalPages > 1 ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => setCurrentPage((value) => Math.max(1, value - 1))}
            disabled={isLoading || currentPage <= 1}
            style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: currentPage <= 1 ? '#E8EEF3' : '#FFFFFF', color: '#0F4C81', padding: '0 18px' }}
          >
            {t('bills.previousPage')}
          </button>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {paginationItems.map((item) => typeof item === 'number' ? (
              <button
                key={item}
                type="button"
                onClick={() => setCurrentPage(item)}
                disabled={isLoading || item === currentPage}
                style={{ minWidth: '40px', minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: item === currentPage ? '#0F4C81' : '#FFFFFF', color: item === currentPage ? '#FFFFFF' : '#0F4C81', padding: '0 12px', fontWeight: 700 }}
              >
                {item}
              </button>
            ) : (
              <span key={item} style={{ color: '#5C6B7A', minWidth: '24px', textAlign: 'center' }}>…</span>
            ))}
            <strong style={{ marginLeft: '8px' }}>{t('bills.paginationLabel', { current: currentPage, total: totalPages })}</strong>
          </div>
          <button
            type="button"
            onClick={() => setCurrentPage((value) => Math.min(totalPages, value + 1))}
            disabled={isLoading || currentPage >= totalPages}
            style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: currentPage >= totalPages ? '#E8EEF3' : '#FFFFFF', color: '#0F4C81', padding: '0 18px' }}
          >
            {t('bills.nextPage')}
          </button>
        </div>
      ) : null}
    </div>
  );
}
