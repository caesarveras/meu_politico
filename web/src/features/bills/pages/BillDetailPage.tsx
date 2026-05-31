import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { apiClient } from '../../../shared/api/client';
import { describeBillStage, describeBillTypeAcronym, describeBodyAcronym, explainBodyAcronym, formatDateTime, formatVotingResult, getBillStageTone, getOfficialBillUrl, getPresidentInOffice, getVotingResultTone } from '../../../shared/bills';
import { Bill } from '../../../shared/types/api';
import { Card } from '../../../shared/ui/Card';
import { InfoHint } from '../../../shared/ui/InfoHint';
import { SectionTitle } from '../../../shared/ui/SectionTitle';

function normalizeVoteGroupLabel(vote: string) {
  const normalized = vote.trim().toLowerCase();
  if (normalized === 'sim') {
    return 'Sim';
  }
  if (normalized === 'não' || normalized === 'nao') {
    return 'Não';
  }
  if (normalized.includes('absten')) {
    return 'Abstenção';
  }
  return vote;
}

function getVoteGroupOrder(label: string) {
  if (label === 'Sim') {
    return 0;
  }
  if (label === 'Não') {
    return 1;
  }
  if (label === 'Abstenção') {
    return 2;
  }
  return 3;
}

function getVoteGroupColor(label: string) {
  if (label === 'Sim') {
    return '#166534';
  }
  if (label === 'Não') {
    return '#B91C1C';
  }
  if (label === 'Abstenção') {
    return '#A16207';
  }
  return '#64748B';
}

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
}

function describePieSlicePath(centerX: number, centerY: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(centerX, centerY, radius, endAngle);
  const end = polarToCartesian(centerX, centerY, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

  return [
    `M ${centerX} ${centerY}`,
    `L ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
    'Z',
  ].join(' ');
}

function formatPercentage(value: number) {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

function extractEmbeddedDateTime(text: string) {
  const match = text.match(/(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})/);
  return match ? match[1] : null;
}

function stripEmbeddedDateTime(text: string) {
  return text.replace(/\s*em\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\.?/i, '.').replace(/\.\./g, '.').trim();
}

function isPartialVetoStage(item: Bill['timeline'][number]) {
  const text = `${item.fase} ${item.descricao}`.toLowerCase();
  return text.includes('transformado em norma jurídica com veto parcial');
}

function getPresidentialDescription(item: Bill['timeline'][number]) {
  const extractedDate = item.data ?? extractEmbeddedDateTime(item.descricao);
  const cleanedDescription = stripEmbeddedDateTime(item.descricao);
  const president = extractedDate ? getPresidentInOffice(extractedDate) : null;
  const formattedDate = extractedDate ? formatDateTime(extractedDate) : null;
  const parts = [cleanedDescription];
  if (president) {
    parts.push(`Presidente em exercício: ${president}.`);
  }
  if (formattedDate) {
    parts.push(`Data e hora: ${formattedDate}.`);
  }
  return parts.join(' ');
}

export function BillDetailPage() {
  const { billId = '' } = useParams();
  const [bill, setBill] = useState<Bill | null>(null);

  useEffect(() => {
    apiClient.getBill<Bill>(billId).then((data) => setBill(data)).catch(() => setBill(null));
  }, [billId]);

  if (!bill) {
    return (
      <Card>
        <p style={{ margin: 0 }}>Não há dados para serem exibidos</p>
      </Card>
    );
  }

  const officialUrl = getOfficialBillUrl(bill);

  return (
    <div style={{ display: 'grid', gap: '24px' }} data-testid="bill-detail-page">
      <Card>
        <SectionTitle
          title={`${bill.sigla} ${bill.numero}/${bill.ano}`}
          subtitle={bill.status_atual}
          action={<InfoHint title={`O que significa ${bill.sigla}?`} body={describeBillTypeAcronym(bill.sigla)} />}
        />
        <p style={{ margin: '16px 0 0' }} data-testid="bill-detail-ementa">{bill.ementa}</p>
        <p style={{ margin: '12px 0 0', color: '#435466' }} data-testid="bill-detail-author">Autor principal: {bill.autor_principal}</p>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
          <a href={officialUrl} target="_blank" rel="noreferrer" style={{ minHeight: '44px', display: 'inline-flex', alignItems: 'center', padding: '0 18px', borderRadius: '999px', background: '#0F4C81', color: '#FFFFFF', textDecoration: 'none' }} data-testid="bill-official-link">
            Ver no site oficial
          </a>
          <Link to="/leis" style={{ minHeight: '44px', display: 'inline-flex', alignItems: 'center', padding: '0 18px', borderRadius: '999px', border: '1px solid #0F4C81', color: '#0F4C81', textDecoration: 'none' }} data-testid="bill-back-link">
            Voltar para leis
          </Link>
        </div>
      </Card>

      <Card>
        <div data-testid="bill-summary-section">
          <SectionTitle title="Resumo" />
          <p style={{ margin: 0 }} data-testid="bill-summary-text">{bill.resumo}</p>
        </div>
      </Card>

      <Card>
        <div data-testid="bill-timeline-section">
          <SectionTitle title="Linha do tempo" />
          <details open style={{ background: '#F8FAFC', borderRadius: '16px', padding: '16px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 700, color: '#0F4C81' }}>
              Abrir linha do tempo completa ({bill.timeline.length} etapa{bill.timeline.length === 1 ? '' : 's'})
            </summary>
            <div style={{ display: 'grid', gap: '12px', marginTop: '16px' }}>
              {bill.timeline.map((item) => (
                <div key={`${item.ordem}-${item.fase}-${item.orgao}`} style={{ paddingBottom: '12px', borderBottom: '1px solid #D7DEE5' }} data-testid="bill-timeline-item">
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <strong>{item.fase}</strong>
                    <InfoHint title={`O que significa esta etapa?`} body={describeBillStage(item.fase, item.descricao)} />
                    {isPartialVetoStage(item) ? (
                      <InfoHint
                        title="O que significa veto parcial?"
                        body="Esse item indica que a proposta virou norma jurídica, mas a Presidência vetou apenas parte do texto aprovado pelo Legislativo. O restante da norma foi sancionado e entrou em vigor conforme a publicação oficial."
                      />
                    ) : null}
                  </div>
                  <p style={{ margin: '6px 0 0', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span>{describeBodyAcronym(item.orgao)}</span>
                    <InfoHint title={`O que significa ${item.orgao}?`} body={explainBodyAcronym(item.orgao)} />
                  </p>
                  {item.data ?? extractEmbeddedDateTime(item.descricao) ? <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>{`Data e hora do trâmite: ${formatDateTime(item.data ?? extractEmbeddedDateTime(item.descricao))}`}</p> : null}
                  {item.relator_name ? (
                    <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>
                      Relator:{' '}
                      {item.relator_id ? (
                        <Link to={`/politicos/${item.relator_id}`} style={{ color: '#16202A', textDecoration: 'none', fontWeight: 700 }} data-testid="bill-relator-link">
                          {item.relator_name}
                        </Link>
                      ) : (
                        item.relator_name
                      )}
                    </p>
                  ) : null}
                  <p style={{ margin: '6px 0 0', color: getBillStageTone(item.fase, item.descricao) === 'approved' ? '#166534' : getBillStageTone(item.fase, item.descricao) === 'rejected' ? '#B91C1C' : '#5C6B7A', fontWeight: item.orgao === 'Presidência da República' ? 700 : 400 }}>
                    {item.orgao === 'Presidência da República' ? getPresidentialDescription(item) : item.descricao}
                  </p>
                </div>
              ))}
            </div>
          </details>
        </div>
      </Card>

      <Card>
        <div data-testid="bill-votes-section">
          <SectionTitle title="Votações" />
          {bill.votacoes.length === 0 ? (
          <p style={{ margin: 0 }}>Não há dados para serem exibidos</p>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {bill.votacoes.map((vote) => (
              <div key={`${vote.id}-${vote.data}`} style={{ paddingBottom: '12px', borderBottom: '1px solid #D7DEE5' }} data-testid="bill-vote-session">
                <strong>{vote.titulo}</strong>
                <p style={{ margin: '6px 0 0' }}>{describeBodyAcronym(vote.orgao)}</p>
                <p style={{ margin: '6px 0 0', color: '#5C6B7A' }}>{formatDateTime(vote.data)}</p>
                <p style={{ margin: '6px 0 0', color: getVotingResultTone(vote.resultado) === 'approved' ? '#166534' : getVotingResultTone(vote.resultado) === 'rejected' ? '#B91C1C' : '#5C6B7A', fontWeight: 700 }}>
                  {formatVotingResult(vote.resultado)}
                </p>
                {vote.votos.length > 0 ? (
                  (() => {
                    const groupedVotes = vote.votos.reduce<Record<string, typeof vote.votos>>((groups, item) => {
                      const label = normalizeVoteGroupLabel(item.voto);
                      if (!groups[label]) {
                        groups[label] = [];
                      }
                      groups[label].push(item);
                      return groups;
                    }, {});
                    const chartEntries = ['Sim', 'Não', 'Abstenção'].map((label) => ({
                      label,
                      count: groupedVotes[label]?.length ?? 0,
                      color: getVoteGroupColor(label),
                    }));
                    const totalChartVotes = chartEntries.reduce((sum, entry) => sum + entry.count, 0);
                    let currentAngle = 0;
                    const chartSlices = chartEntries
                      .filter((entry) => entry.count > 0)
                      .map((entry) => {
                        const percentage = totalChartVotes === 0 ? 0 : (entry.count / totalChartVotes) * 100;
                        const sliceAngle = (percentage / 100) * 360;
                        const startAngle = currentAngle;
                        const endAngle = currentAngle + sliceAngle;
                        currentAngle = endAngle;
                        return {
                          ...entry,
                          percentage,
                          path: describePieSlicePath(60, 60, 52, startAngle, endAngle),
                        };
                      });

                    return (
                      <div style={{ display: 'grid', gap: '12px', marginTop: '12px' }}>
                        <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'minmax(140px, 180px) 1fr', alignItems: 'center', background: '#F8FAFC', borderRadius: '16px', padding: '16px' }} data-testid="bill-vote-pie-chart">
                          <div style={{ display: 'flex', justifyContent: 'center' }}>
                            <svg viewBox="0 0 120 120" width="140" height="140" aria-label="Distribuição percentual dos votos sim, não e abstenção">
                              {chartSlices.length > 0 ? chartSlices.map((slice) => (
                                <path key={`${vote.id}-${slice.label}`} d={slice.path} fill={slice.color} stroke="#FFFFFF" strokeWidth="2" />
                              )) : <circle cx="60" cy="60" r="52" fill="#E2E8F0" />}
                              <circle cx="60" cy="60" r="26" fill="#FFFFFF" />
                              <text x="60" y="56" textAnchor="middle" style={{ fill: '#16202A', fontSize: '12px', fontWeight: 700 }}>
                                Votos
                              </text>
                              <text x="60" y="72" textAnchor="middle" style={{ fill: '#5C6B7A', fontSize: '12px' }}>
                                {totalChartVotes}
                              </text>
                            </svg>
                          </div>
                          <div style={{ display: 'grid', gap: '10px' }}>
                            {chartEntries.map((entry) => {
                              const percentage = totalChartVotes === 0 ? 0 : (entry.count / totalChartVotes) * 100;
                              return (
                                <div key={`${vote.id}-${entry.label}-legend`} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={{ width: '12px', height: '12px', borderRadius: '999px', background: entry.color, display: 'inline-block' }} />
                                    <strong>{entry.label}</strong>
                                  </div>
                                  <span style={{ color: '#435466' }}>
                                    {entry.count} voto{entry.count === 1 ? '' : 's'} · {formatPercentage(percentage)}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        {Object.entries(groupedVotes)
                          .sort(([left], [right]) => getVoteGroupOrder(left) - getVoteGroupOrder(right))
                          .map(([groupLabel, records]) => (
                            <details key={`${vote.id}-${groupLabel}`} style={{ background: '#F8FAFC', borderRadius: '16px', padding: '12px' }} data-testid="bill-vote-group">
                              <summary style={{ cursor: 'pointer', fontWeight: 700 }}>
                                {groupLabel} ({records.length})
                              </summary>
                              <div style={{ display: 'grid', gap: '8px', marginTop: '12px' }}>
                                {records.map((record) => (
                                  <div key={`${vote.id}-${groupLabel}-${record.politician_id ?? record.politician_name}`} style={{ borderBottom: '1px solid #D7DEE5', paddingBottom: '8px' }} data-testid="bill-vote-record">
                                    {record.politician_id ? (
                                      <Link to={`/politicos/${record.politician_id}`} style={{ fontWeight: 700, color: '#16202A', textDecoration: 'none' }} data-testid="bill-vote-politician-link">
                                        {record.politician_name}
                                      </Link>
                                    ) : (
                                      <strong>{record.politician_name}</strong>
                                    )}
                                    <p style={{ margin: '4px 0 0', color: '#5C6B7A' }}>
                                      {[record.partido, record.uf, record.cidade].filter(Boolean).join(' · ') || 'Partido/UF/cidade não informados'}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </details>
                          ))}
                      </div>
                    );
                  })()
                ) : (
                  <p style={{ margin: '12px 0 0', color: '#5C6B7A' }}>Não há votos nominais disponíveis para esta votação.</p>
                )}
              </div>
            ))}
          </div>
        )}
        </div>
      </Card>
    </div>
  );
}
