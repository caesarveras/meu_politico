import { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { apiClient } from '../../../shared/api/client';
import { ApprovedBillsSearchResponse, Bill } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { Pagination } from '../../../shared/ui/Pagination';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

type Highlight = { title: string; subtitle: string; metric: string };

function getHighlightMetric(highlights: Highlight[], index: number) {
  return highlights[index]?.metric ?? '0';
}

export function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [approvedBills, setApprovedBills] = useState<Bill[]>([]);
  const [approvedBillsTotal, setApprovedBillsTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [historySortOrder, setHistorySortOrder] = useState<'desc' | 'asc'>('desc');
  const [isLoadingBills, setIsLoadingBills] = useState(false);
  const historyPerPage = 4;

  const loadApprovedBills = async (page: number, theme?: string, sortOrder?: 'desc' | 'asc') => {
    setIsLoadingBills(true);
    try {
      const response = await apiClient.searchApprovedBills<ApprovedBillsSearchResponse>({
        theme: theme?.trim() || undefined,
        page,
        page_size: historyPerPage,
        sort_by: sortOrder === 'asc' ? 'oldest' : 'newest',
      });
      setApprovedBills(response.data);
      setApprovedBillsTotal(response.meta.total_count);
    } catch {
      setApprovedBills([]);
      setApprovedBillsTotal(0);
    } finally {
      setIsLoadingBills(false);
    }
  };

  useEffect(() => {
    apiClient.getHighlights<Highlight[]>().then((data) => setHighlights(data)).catch(() => setHighlights([]));
    void loadApprovedBills(1, '', 'desc');
  }, []);

  useEffect(() => {
    setHistoryPage(1);
  }, [historySortOrder, query]);

  useEffect(() => {
    void loadApprovedBills(historyPage, query, historySortOrder);
  }, [historyPage, historySortOrder]);

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setHistoryPage(1);
    await loadApprovedBills(1, query, historySortOrder);
  };

  const totalHistoryPages = Math.max(1, Math.ceil(approvedBillsTotal / historyPerPage));
  const currentHistoryPage = Math.min(historyPage, totalHistoryPages);

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="home-page">
      <Card>
        <div style={{ display: 'grid', gap: '24px', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', alignItems: 'start' }}>
          <div style={{ display: 'grid', gap: '18px' }}>
            <div style={{ display: 'grid', gap: '10px' }}>
              <p style={{ margin: 0, color: '#0F4C81', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: '0.82rem' }}>{t('home.heroEyebrow')}</p>
              <h2 style={{ margin: 0, fontSize: 'clamp(2rem, 3.2vw, 3rem)', lineHeight: 1.05, color: '#16202A' }}>{t('home.heroTitle')}</h2>
              <p style={{ margin: 0, color: '#435466', fontSize: '1.02rem', maxWidth: '720px' }}>{t('home.heroBody')}</p>
            </div>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button type="button" onClick={() => navigate('/leis-aprovadas')} style={{ minHeight: '46px', borderRadius: '999px', border: 'none', background: '#0F4C81', color: '#FFFFFF', padding: '0 18px', fontWeight: 700 }} data-testid="home-hero-bills-cta">{t('home.heroPrimaryCta')}</button>
              <button type="button" onClick={() => navigate('/leis')} style={{ minHeight: '46px', borderRadius: '999px', border: '1px solid #0F4C81', background: '#FFFFFF', color: '#0F4C81', padding: '0 18px', fontWeight: 700 }} data-testid="home-hero-all-bills-cta">{t('home.heroAllBillsCta')}</button>
              <button type="button" onClick={() => navigate('/parlamentares')} style={{ minHeight: '46px', borderRadius: '999px', border: '1px solid #0F4C81', background: '#FFFFFF', color: '#0F4C81', padding: '0 18px', fontWeight: 700 }} data-testid="home-hero-politicians-cta">{t('home.heroSecondaryCta')}</button>
            </div>
            <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
              {[
                { metric: getHighlightMetric(highlights, 0), label: t('home.heroStatOneLabel') },
                { metric: String(approvedBillsTotal), label: t('home.heroStatTwoLabel') },
                { metric: getHighlightMetric(highlights, 2), label: t('home.heroStatThreeLabel') },
              ].map((item) => (
                <div key={item.label} style={{ border: '1px solid #D7DEE5', borderRadius: '18px', padding: '16px 18px', background: '#F8FBFF' }}>
                  <strong style={{ display: 'block', fontSize: '1.7rem', color: '#0F4C81' }}>{item.metric}</strong>
                  <span style={{ color: '#435466' }}>{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gap: '16px', alignContent: 'start', padding: '20px', borderRadius: '20px', background: 'linear-gradient(180deg, #F7FAFC 0%, #EEF4F8 100%)', border: '1px solid #D7DEE5' }}>
            <SectionTitle title={t('home.title')} subtitle={t('home.subtitle')} />
            <form onSubmit={handleSearch} style={{ display: 'grid', gap: '14px' }} data-testid="home-search-form">
              <label style={{ display: 'grid', gap: '8px' }}>
                <span>{t('home.searchLabel')}</span>
                <input data-testid="home-search-input" value={query} onChange={(event: ChangeEvent<HTMLInputElement>) => setQuery(event.target.value)} disabled={isLoadingBills} placeholder={t('home.searchPlaceholder')} style={{ minHeight: '44px', borderRadius: '12px', border: '1px solid #D7DEE5', padding: '0 12px', background: '#FFFFFF' }} />
              </label>
              <p style={{ margin: 0, color: '#5C6B7A', fontSize: '0.94rem' }}>{t('home.searchHelp')}</p>
              {isLoadingBills ? <p style={{ margin: 0, color: '#5C6B7A', fontSize: '0.94rem' }}>{t('home.loadingBills')}</p> : null}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'end', flexWrap: 'wrap' }}>
                <button type="submit" disabled={isLoadingBills} style={{ minHeight: '44px', borderRadius: '999px', border: 'none', background: '#0F4C81', color: '#FFFFFF', padding: '0 18px' }} data-testid="home-search-submit">Buscar</button>
                <button type="button" onClick={() => navigate('/parlamentares')} disabled={isLoadingBills} style={{ minHeight: '44px', borderRadius: '999px', border: '1px solid #0F4C81', background: '#FFFFFF', color: '#0F4C81', padding: '0 18px' }} data-testid="home-open-politicians">{t('home.openSearch')}</button>
              </div>
            </form>
          </div>
        </div>
      </Card>

      <section data-testid="home-highlights-section">
        <SectionTitle
         title={t('home.approvedTitle')}
         subtitle={t('home.exploreSubtitle')}
         action={<InfoHint title={t('education.approvedLawsTitle')} body={t('education.approvedLawsBody')} />}
       />
        {highlights.length === 0 ? (
          <Card>
            <p style={{ margin: 0 }}>Não há dados para serem exibidos</p>
          </Card>
        ) : (
          <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
            {highlights.map((item) => (
              <Card key={item.title}>
                <div data-testid="highlight-card">
                  <strong style={{ fontSize: '2rem', color: '#1B7F5A' }}>{item.metric}</strong>
                  <p style={{ margin: '8px 0 0' }}>{item.title}</p>
                  <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>{item.subtitle}</p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section data-testid="home-explore-section">
        <SectionTitle title={t('home.exploreTitle')} subtitle={t('home.exploreSubtitle')} />
        <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <Card>
            <div style={{ display: 'grid', gap: '12px' }}>
              <h3 style={{ margin: 0 }}>{t('home.exploreBillsTitle')}</h3>
              <p style={{ margin: 0, color: '#5C6B7A' }}>{t('home.exploreAllBillsBody')}</p>
              <div>
                <Link to="/leis" style={{ color: '#0F4C81', fontWeight: 700, textDecoration: 'none' }}>{t('home.exploreAllBillsCta')}</Link>
              </div>
            </div>
          </Card>
          <Card>
            <div style={{ display: 'grid', gap: '12px' }}>
              <h3 style={{ margin: 0 }}>{t('home.explorePoliticiansTitle')}</h3>
              <p style={{ margin: 0, color: '#5C6B7A' }}>{t('home.explorePoliticiansBody')}</p>
              <div>
                <Link to="/parlamentares" style={{ color: '#0F4C81', fontWeight: 700, textDecoration: 'none' }}>{t('home.explorePoliticiansCta')}</Link>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <section data-testid="home-approved-bills-section">
        <SectionTitle
         title={t('home.historyTitle')}
         action={<InfoHint title={t('education.legislativeFlowTitle')} body={t('education.legislativeFlowBody')} />}
       />
        {approvedBills.length === 0 ? (
          <Card>
            <p style={{ margin: 0 }}>{query.trim() ? t('home.noSearchResults') : t('home.empty')}</p>
          </Card>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '16px' }}>
              <button type="button" onClick={() => setHistorySortOrder('desc')} disabled={isLoadingBills || historySortOrder === 'desc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: historySortOrder === 'desc' ? '#0F4C81' : '#FFFFFF', color: historySortOrder === 'desc' ? '#FFFFFF' : '#0F4C81' }}>
                {t('home.historySortNewest')}
              </button>
              <button type="button" onClick={() => setHistorySortOrder('asc')} disabled={isLoadingBills || historySortOrder === 'asc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: historySortOrder === 'asc' ? '#0F4C81' : '#FFFFFF', color: historySortOrder === 'asc' ? '#FFFFFF' : '#0F4C81' }}>
                {t('home.historySortOldest')}
              </button>
              <span style={{ marginLeft: 'auto', color: '#5C6B7A', fontSize: '0.95rem' }}>
                {approvedBillsTotal} {t('home.resultsLabel')}
              </span>
            </div>
            <div style={{ display: 'grid', gap: '16px' }}>
              {approvedBills.map((bill) => (
                <Card key={bill.id}>
                  <div data-testid="home-approved-bill-card">
                    <Link to={`/leis/${bill.id}`} style={{ margin: 0, color: '#1B7F5A', fontWeight: 700, textDecoration: 'none' }} data-testid="home-approved-bill-link">{bill.sigla} {bill.numero}/{bill.ano}</Link>
                    <h3 style={{ marginBottom: '8px' }}><Link to={`/leis/${bill.id}`} style={{ color: '#16202A', textDecoration: 'none' }}>{bill.ementa}</Link></h3>
                    <p style={{ margin: '0 0 8px', color: '#435466' }}>{t('bills.authorLabel')}: {bill.autor_principal}</p>
                    <p style={{ margin: 0, color: '#5C6B7A' }}>{bill.status_atual}</p>
                  </div>
                </Card>
              ))}
            </div>
            <div style={{ display: 'grid', gap: '8px', marginTop: '16px' }}>
              <Pagination currentPage={currentHistoryPage} totalPages={totalHistoryPages} onPageChange={setHistoryPage} />
              <span style={{ textAlign: 'center', color: '#5C6B7A', fontSize: '0.95rem' }}>{`Página ${currentHistoryPage} de ${totalHistoryPages}`}</span>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
