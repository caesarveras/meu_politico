import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { apiClient } from '../../../shared/api/client';
import { formatDate, formatVotingResult, getVotingResultTone } from '../../../shared/bills';
import { PoliticianHistory } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { Pagination } from '../../../shared/ui/Pagination';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

type RelatedBillsFilter = 'all' | 'authored' | 'approved_by_politician' | 'rejected_by_politician' | 'approved_enacted';

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

export function PoliticianHistoryPage() {
  const { t } = useTranslation();
  const { politicianId = '1' } = useParams();
  const [history, setHistory] = useState<PoliticianHistory | null>(null);
  const [timelinePage, setTimelinePage] = useState(1);
  const [timelineSortOrder, setTimelineSortOrder] = useState<'desc' | 'asc'>('desc');
  const [votesPage, setVotesPage] = useState(1);
  const [votesSortOrder, setVotesSortOrder] = useState<'desc' | 'asc'>('desc');
  const [relatedBillsFilter, setRelatedBillsFilter] = useState<RelatedBillsFilter>('all');
  const timelinePerPage = 10;
  const votesPerPage = 10;

  useEffect(() => {
    apiClient.getPoliticianHistory<PoliticianHistory>(politicianId).then((data) => setHistory(data)).catch(() => setHistory(null));
  }, [politicianId]);

  useEffect(() => {
    setVotesPage(1);
  }, [politicianId, votesSortOrder]);

  useEffect(() => {
    setTimelinePage(1);
  }, [politicianId, timelineSortOrder]);

  const timelineItems = history?.timeline ?? [];
  const votingHistory = history?.voting_history ?? [];
  const approvedBills = history?.approved_bills_related ?? [];

  const sortedTimelineItems = useMemo(() => {
    return [...timelineItems].sort((left, right) => {
      const leftValue = left.data ? new Date(left.data).getTime() : 0;
      const rightValue = right.data ? new Date(right.data).getTime() : 0;
      return timelineSortOrder === 'desc' ? rightValue - leftValue : leftValue - rightValue;
    });
  }, [timelineItems, timelineSortOrder]);

  const sortedVotingHistory = useMemo(() => {
    return [...votingHistory].sort((left, right) => {
      const leftValue = left.data ? new Date(left.data).getTime() : 0;
      const rightValue = right.data ? new Date(right.data).getTime() : 0;
      return votesSortOrder === 'desc' ? rightValue - leftValue : leftValue - rightValue;
    });
  }, [votingHistory, votesSortOrder]);

  const filteredApprovedBills = useMemo(() => {
    if (relatedBillsFilter === 'all') {
      return approvedBills;
    }
    return approvedBills.filter((bill) => bill.related_to_politician_as.includes(relatedBillsFilter));
  }, [approvedBills, relatedBillsFilter]);

  const totalTimelinePages = Math.max(1, Math.ceil(sortedTimelineItems.length / timelinePerPage));
  const currentTimelinePage = Math.min(timelinePage, totalTimelinePages);
  const paginatedTimelineItems = sortedTimelineItems.slice((currentTimelinePage - 1) * timelinePerPage, currentTimelinePage * timelinePerPage);
  const totalVotesPages = Math.max(1, Math.ceil(sortedVotingHistory.length / votesPerPage));
  const currentVotesPage = Math.min(votesPage, totalVotesPages);
  const paginatedVotingHistory = sortedVotingHistory.slice((currentVotesPage - 1) * votesPerPage, currentVotesPage * votesPerPage);

  if (!history) {
    return (
      <Card>
        <p style={{ margin: 0 }}>{t('politician.empty')}</p>
      </Card>
    );
  }

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="politician-history-page">
      <Card>
        <div data-testid="politician-history-header">
          <SectionTitle
            title={t('politician.title')}
            subtitle={`${history.politician.nome} · ${history.politician.cargo} · ${history.politician.partido}/${history.politician.uf}`}
            action={<InfoHint title={t('education.rolesTitle')} body={t('education.rolesBody')} />}
          />
          <p style={{ margin: '0 0 6px', color: '#5C6B7A' }}>{history.politician.cidade ?? 'Cidade não informada'}</p>
          <p style={{ margin: 0, ...getPoliticianStatusStyle(history.politician.status_politico) }}>{history.politician.status_politico}</p>
        </div>
      </Card>

      <Card>
        <div data-testid="politician-history-content">
          <SectionTitle
            title="Timeline"
            action={<InfoHint title="O que é a timeline?" body="A timeline reúne, em ordem cronológica, marcos relevantes da atuação pública e legislativa associados a este parlamentar." />}
          />
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '16px' }}>
            <button type="button" onClick={() => setTimelineSortOrder('desc')} disabled={timelineSortOrder === 'desc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: timelineSortOrder === 'desc' ? '#0F4C81' : '#FFFFFF', color: timelineSortOrder === 'desc' ? '#FFFFFF' : '#0F4C81' }}>
              Mais recentes primeiro
            </button>
            <button type="button" onClick={() => setTimelineSortOrder('asc')} disabled={timelineSortOrder === 'asc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: timelineSortOrder === 'asc' ? '#0F4C81' : '#FFFFFF', color: timelineSortOrder === 'asc' ? '#FFFFFF' : '#0F4C81' }}>
              Mais antigas primeiro
            </button>
          </div>
          {timelineItems.length === 0 ? (
            <p style={{ margin: '0 0 16px' }}>Não há dados para serem exibidos</p>
          ) : (
            <>
              <div style={{ display: 'grid', gap: '12px', marginBottom: '24px' }} data-testid="politician-timeline-list">
                {paginatedTimelineItems.map((item) => (
                  <div key={`${item.ordem}-${item.titulo}-${item.data}`} style={{ paddingBottom: '12px', borderBottom: '1px solid #D7DEE5' }} data-testid="politician-timeline-item">
                    <strong>{item.titulo}</strong>
                    <p style={{ margin: '6px 0 0' }}>{item.descricao}</p>
                    <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>
                      {formatDate(item.data)}
                      {item.orgao ? ` · ${item.orgao}` : ''}
                      {item.legislatura ? ` · Legislatura ${item.legislatura}` : ''}
                    </p>
                  </div>
                ))}
              </div>
              <div style={{ display: 'grid', gap: '8px', marginBottom: '24px' }}>
                <Pagination currentPage={currentTimelinePage} totalPages={totalTimelinePages} onPageChange={setTimelinePage} />
                <span style={{ textAlign: 'center', color: '#5C6B7A' }}>{`Página ${currentTimelinePage} de ${totalTimelinePages}`}</span>
              </div>
            </>
          )}

          <SectionTitle
            title={t('politician.votesTitle')}
            action={<InfoHint title={t('education.votingHistoryTitle')} body={t('education.votingHistoryBody')} />}
          />
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '16px' }}>
            <button type="button" onClick={() => setVotesSortOrder('desc')} disabled={votesSortOrder === 'desc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: votesSortOrder === 'desc' ? '#0F4C81' : '#FFFFFF', color: votesSortOrder === 'desc' ? '#FFFFFF' : '#0F4C81' }}>
              Mais recentes primeiro
            </button>
            <button type="button" onClick={() => setVotesSortOrder('asc')} disabled={votesSortOrder === 'asc'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: votesSortOrder === 'asc' ? '#0F4C81' : '#FFFFFF', color: votesSortOrder === 'asc' ? '#FFFFFF' : '#0F4C81' }}>
              Mais antigos primeiro
            </button>
          </div>
          {votingHistory.length === 0 ? (
            <p style={{ margin: 0 }}>Não há dados para serem exibidos</p>
          ) : (
            <>
              <div style={{ display: 'grid', gap: '12px' }} data-testid="politician-voting-history-list">
                {paginatedVotingHistory.map((item: PoliticianHistory['voting_history'][number]) => (
                  <div key={`${item.bill_label}-${item.votacao_id}-${item.data}`} style={{ paddingBottom: '12px', borderBottom: '1px solid #D7DEE5' }} data-testid="politician-voting-history-item">
                    {item.bill_id ? <Link to={`/leis/${item.bill_id}`} style={{ fontWeight: 700, color: '#16202A', textDecoration: 'none' }}>{item.bill_label}</Link> : <strong>{item.bill_label}</strong>}
                    {item.bill_text ? <p style={{ margin: '6px 0 0' }}>{item.bill_text}</p> : null}
                    <p style={{ margin: '6px 0 0' }}>{item.voto} · {item.orgao}</p>
                    <p style={{ margin: '6px 0 0' }}>
                      <span style={{ color: '#5C6B7A' }}>{formatDate(item.data)} · </span>
                      <span style={{ color: getVotingResultTone(item.resultado) === 'approved' ? '#166534' : getVotingResultTone(item.resultado) === 'rejected' ? '#B91C1C' : '#5C6B7A', fontWeight: 700 }}>
                        {formatVotingResult(item.resultado)}
                      </span>
                    </p>
                  </div>
                ))}
              </div>
              <div style={{ display: 'grid', gap: '8px', marginTop: '16px' }}>
                <Pagination currentPage={currentVotesPage} totalPages={totalVotesPages} onPageChange={setVotesPage} />
                <span style={{ textAlign: 'center', color: '#5C6B7A' }}>{`Página ${currentVotesPage} de ${totalVotesPages}`}</span>
              </div>
            </>
          )}
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={t('politician.relatedBillsTitle')}
          action={<InfoHint title={t('education.approvedLawsTitle')} body={t('education.approvedLawsBody')} />}
        />
        {approvedBills.length === 0 ? (
          <p style={{ margin: 0 }}>Não há dados para serem exibidos</p>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
              <button type="button" onClick={() => setRelatedBillsFilter('all')} disabled={relatedBillsFilter === 'all'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: relatedBillsFilter === 'all' ? '#0F4C81' : '#FFFFFF', color: relatedBillsFilter === 'all' ? '#FFFFFF' : '#0F4C81' }}>
                {t('politician.relatedBillsAll')}
              </button>
              <button type="button" onClick={() => setRelatedBillsFilter('authored')} disabled={relatedBillsFilter === 'authored'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: relatedBillsFilter === 'authored' ? '#0F4C81' : '#FFFFFF', color: relatedBillsFilter === 'authored' ? '#FFFFFF' : '#0F4C81' }}>
                {t('politician.relatedBillsAuthored')}
              </button>
              <button type="button" onClick={() => setRelatedBillsFilter('approved_by_politician')} disabled={relatedBillsFilter === 'approved_by_politician'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: relatedBillsFilter === 'approved_by_politician' ? '#0F4C81' : '#FFFFFF', color: relatedBillsFilter === 'approved_by_politician' ? '#FFFFFF' : '#0F4C81' }}>
                {t('politician.relatedBillsApprovedByPolitician')}
              </button>
              <button type="button" onClick={() => setRelatedBillsFilter('rejected_by_politician')} disabled={relatedBillsFilter === 'rejected_by_politician'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: relatedBillsFilter === 'rejected_by_politician' ? '#0F4C81' : '#FFFFFF', color: relatedBillsFilter === 'rejected_by_politician' ? '#FFFFFF' : '#0F4C81' }}>
                {t('politician.relatedBillsRejectedByPolitician')}
              </button>
              <button type="button" onClick={() => setRelatedBillsFilter('approved_enacted')} disabled={relatedBillsFilter === 'approved_enacted'} style={{ minHeight: '36px', padding: '0 12px', borderRadius: '999px', border: '1px solid #0F4C81', background: relatedBillsFilter === 'approved_enacted' ? '#0F4C81' : '#FFFFFF', color: relatedBillsFilter === 'approved_enacted' ? '#FFFFFF' : '#0F4C81' }}>
                {t('politician.relatedBillsApprovedEnacted')}
              </button>
            </div>
            <div style={{ display: 'grid', gap: '12px' }} data-testid="politician-related-bills-list">
            {filteredApprovedBills.map((bill: PoliticianHistory['approved_bills_related'][number]) => (
              <div key={bill.id} style={{ paddingBottom: '12px', borderBottom: '1px solid #D7DEE5' }} data-testid="politician-related-bill-item">
                <Link to={`/leis/${bill.id}`} style={{ fontWeight: 700, color: '#16202A', textDecoration: 'none' }}>{bill.sigla} {bill.numero}/{bill.ano}</Link>
                <p style={{ margin: '6px 0 0' }}>{bill.ementa}</p>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                  {bill.related_to_politician_as.includes('authored') ? <span style={{ padding: '4px 10px', borderRadius: '999px', background: '#DBEAFE', color: '#1D4ED8', fontSize: '0.85rem', fontWeight: 700 }}>{t('politician.relatedBillAuthoredBadge')}</span> : null}
                  {bill.related_to_politician_as.includes('approved_by_politician') ? <span style={{ padding: '4px 10px', borderRadius: '999px', background: '#DCFCE7', color: '#166534', fontSize: '0.85rem', fontWeight: 700 }}>{t('politician.relatedBillApprovedByPoliticianBadge')}</span> : null}
                  {bill.related_to_politician_as.includes('rejected_by_politician') ? <span style={{ padding: '4px 10px', borderRadius: '999px', background: '#FEE2E2', color: '#B91C1C', fontSize: '0.85rem', fontWeight: 700 }}>{t('politician.relatedBillRejectedByPoliticianBadge')}</span> : null}
                  {bill.related_to_politician_as.includes('approved_enacted') ? <span style={{ padding: '4px 10px', borderRadius: '999px', background: '#ECFCCB', color: '#3F6212', fontSize: '0.85rem', fontWeight: 700 }}>{t('politician.relatedBillApprovedEnactedBadge')}</span> : null}
                </div>
              </div>
            ))}
            </div>
            {filteredApprovedBills.length === 0 ? <p style={{ margin: '16px 0 0', color: '#5C6B7A' }}>{t('politician.relatedBillsEmpty')}</p> : null}
          </>
        )}
      </Card>
    </div>
  );
}
