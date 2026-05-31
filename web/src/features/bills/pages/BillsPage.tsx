import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { apiClient } from '../../../shared/api/client';
import { Bill } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

const PAGE_SIZE = 12;

export function BillsPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [bills, setBills] = useState<Bill[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    apiClient.getBills<Bill[]>()
      .then((data) => setBills(data))
      .catch(() => setBills([]))
      .finally(() => setIsLoading(false));
  }, []);

  const statusOptions = useMemo(
    () => Array.from(new Set(bills.map((bill) => bill.status_atual).filter(Boolean))).sort((left, right) => left.localeCompare(right, 'pt-BR')),
    [bills],
  );

  const typeOptions = useMemo(
    () => Array.from(new Set(bills.map((bill) => bill.sigla).filter(Boolean))).sort((left, right) => left.localeCompare(right, 'pt-BR')),
    [bills],
  );

  const filteredBills = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return bills.filter((bill) => {
      if (statusFilter && bill.status_atual !== statusFilter) {
        return false;
      }
      if (typeFilter && bill.sigla !== typeFilter) {
        return false;
      }
      if (!normalizedQuery) {
        return true;
      }
      return [bill.sigla, String(bill.numero), String(bill.ano), bill.ementa, bill.resumo, bill.autor_principal, bill.tema, bill.status_atual]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedQuery));
    });
  }, [bills, query, statusFilter, typeFilter]);

  const sortedBills = useMemo(() => {
    return [...filteredBills].sort((left, right) => {
      const leftValue = left.data_apresentacao ? new Date(left.data_apresentacao).getTime() : left.ano;
      const rightValue = right.data_apresentacao ? new Date(right.data_apresentacao).getTime() : right.ano;
      return sortOrder === 'desc' ? rightValue - leftValue : leftValue - rightValue;
    });
  }, [filteredBills, sortOrder]);

  const totalCount = sortedBills.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const currentSafePage = Math.min(currentPage, totalPages);
  const paginatedBills = sortedBills.slice((currentSafePage - 1) * PAGE_SIZE, currentSafePage * PAGE_SIZE);
  const currentRangeStart = totalCount === 0 ? 0 : (currentSafePage - 1) * PAGE_SIZE + 1;
  const currentRangeEnd = totalCount === 0 ? 0 : currentRangeStart + paginatedBills.length - 1;

  useEffect(() => {
    setCurrentPage(1);
  }, [query, statusFilter, typeFilter, sortOrder]);

  const handleResetFilters = () => {
    setQuery('');
    setStatusFilter('');
    setTypeFilter('');
    setSortOrder('desc');
    setCurrentPage(1);
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="bills-page">
      <Card>
        <SectionTitle
          title={t('bills.allTitle')}
          subtitle={t('bills.allSubtitle')}
          action={<InfoHint title={t('education.billStatusTitle')} body={t('education.billStatusBody')} />}
        />
        <div style={{ display: 'grid', gap: '12px' }} data-testid="bills-search-form">
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.generalSearchLabel')}</span>
              <input
                data-testid="bills-query-input"
                value={query}
                onChange={(event: ChangeEvent<HTMLInputElement>) => setQuery(event.target.value)}
                disabled={isLoading}
                placeholder={t('bills.generalSearchPlaceholder')}
                style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px' }}
              />
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.typeLabel')}</span>
              <select data-testid="bills-type-select" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allTypes')}</option>
                {typeOptions.map((type) => <option key={type} value={type}>{type}</option>)}
              </select>
            </label>
            <label style={{ display: 'grid', gap: '8px' }}>
              <span>{t('bills.statusLabel')}</span>
              <select data-testid="bills-status-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} disabled={isLoading} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }}>
                <option value="">{t('bills.allStatuses')}</option>
                {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </label>
          </div>
          {isLoading ? <p style={{ margin: 0, color: '#5C6B7A' }} data-testid="bills-loading">{t('bills.loading')}</p> : null}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: '4px' }}>
              <span style={{ color: '#5C6B7A', fontSize: '0.95rem' }}>{totalCount} {t('bills.resultsCount')}</span>
              <span style={{ color: '#7A8896', fontSize: '0.88rem' }}>{t('bills.resultsSummary', { from: currentRangeStart, to: currentRangeEnd, total: totalCount })}</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button type="button" onClick={() => setSortOrder('desc')} disabled={isLoading || sortOrder === 'desc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: sortOrder === 'desc' ? '#0F4C81' : '#FFFFFF', color: sortOrder === 'desc' ? '#FFFFFF' : '#0F4C81' }}>
                {t('home.historySortNewest')}
              </button>
              <button type="button" onClick={() => setSortOrder('asc')} disabled={isLoading || sortOrder === 'asc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: sortOrder === 'asc' ? '#0F4C81' : '#FFFFFF', color: sortOrder === 'asc' ? '#FFFFFF' : '#0F4C81' }}>
                {t('home.historySortOldest')}
              </button>
              <button type="button" onClick={handleResetFilters} disabled={isLoading || (!query && !statusFilter && !typeFilter && sortOrder === 'desc')} style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: '#FFFFFF', color: '#0F4C81', padding: '0 18px' }} data-testid="bills-clear-filters">{t('bills.clearFilters')}</button>
            </div>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <div style={{ display: 'grid', gap: '16px' }} data-testid="bills-skeleton-list">
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
      ) : paginatedBills.length === 0 ? (
        <Card>
          <p style={{ margin: 0 }}>{t('bills.empty')}</p>
        </Card>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }} data-testid="bills-list">
          {paginatedBills.map((bill: Bill) => (
            <Card key={bill.id}>
              <div data-testid="bill-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'start', flexWrap: 'wrap' }}>
                  <div>
                    <Link to={`/leis/${bill.id}`} style={{ margin: 0, color: '#1B7F5A', fontWeight: 700, textDecoration: 'none' }}>{bill.sigla} {bill.numero}/{bill.ano}</Link>
                    <h3 style={{ marginBottom: '8px' }}><Link to={`/leis/${bill.id}`} style={{ color: '#16202A', textDecoration: 'none' }}>{bill.ementa}</Link></h3>
                    <p style={{ margin: '0 0 8px', color: '#435466' }}>{t('bills.authorLabel')}: {bill.autor_principal}</p>
                    <p style={{ margin: 0, color: '#5C6B7A' }}>{bill.status_atual}</p>
                  </div>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    <span style={{ color: bill.aprovada ? '#1D7A46' : '#B7791F', fontWeight: 700 }}>{bill.aprovada ? t('bills.approved') : t('bills.inProgress')}</span>
                    <Link to={`/leis/${bill.id}`} style={{ color: '#0F4C81' }} data-testid="bill-open-detail">{t('bills.openDetail')}</Link>
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
            disabled={isLoading || currentSafePage <= 1}
            style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: currentSafePage <= 1 ? '#E8EEF3' : '#FFFFFF', color: '#0F4C81', padding: '0 18px' }}
          >
            {t('bills.previousPage')}
          </button>
          <strong>{t('bills.paginationLabel', { current: currentSafePage, total: totalPages })}</strong>
          <button
            type="button"
            onClick={() => setCurrentPage((value) => Math.min(totalPages, value + 1))}
            disabled={isLoading || currentSafePage >= totalPages}
            style={{ minHeight: '40px', borderRadius: '999px', border: '1px solid #0F4C81', background: currentSafePage >= totalPages ? '#E8EEF3' : '#FFFFFF', color: '#0F4C81', padding: '0 18px' }}
          >
            {t('bills.nextPage')}
          </button>
        </div>
      ) : null}
    </div>
  );
}
