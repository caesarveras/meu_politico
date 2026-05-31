import { extractEmbeddedDateTime, formatVotingResult, normalizeApiDateValue, stripEmbeddedDateTime } from '../bills';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, transform?: (payload: unknown) => T): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Falha ao consultar ${path}`);
  }
  const payload = await response.json();
  return transform ? transform(payload) : (payload as T);
}

function normalizeVoteRecord(record: any) {
  return {
    ...record,
    politician_id: typeof record?.politician_id === 'number' ? record.politician_id : null,
    politician_name: record?.politician_name ?? 'Parlamentar não informado',
    voto: record?.voto ?? 'Não informado',
  };
}

function normalizeApprovedBillsSearchResponse(payload: any) {
  return {
    data: Array.isArray(payload?.data) ? payload.data.map(normalizeBill) : [],
    meta: {
      count: typeof payload?.meta?.count === 'number' ? payload.meta.count : 0,
      total_count: typeof payload?.meta?.total_count === 'number' ? payload.meta.total_count : 0,
      page: typeof payload?.meta?.page === 'number' ? payload.meta.page : 1,
      page_size: typeof payload?.meta?.page_size === 'number' ? payload.meta.page_size : 12,
      total_pages: typeof payload?.meta?.total_pages === 'number' ? payload.meta.total_pages : 0,
      schema: payload?.meta?.schema ?? 'public-approved-bills-search-v1',
    },
  };
}

function normalizeVoteSession(session: any) {
  return {
    ...session,
    data: normalizeApiDateValue(session?.data),
    resultado: formatVotingResult(session?.resultado),
    votos: Array.isArray(session?.votos) ? session.votos.map(normalizeVoteRecord) : [],
  };
}

function normalizeBillStage(stage: any) {
  const extractedDate = normalizeApiDateValue(stage?.data) ?? extractEmbeddedDateTime(stage?.descricao);
  const cleanedDescription = extractedDate ? stripEmbeddedDateTime(stage?.descricao) : (stage?.descricao ?? 'Descrição não informada');
  return {
    ...stage,
    data: extractedDate,
    descricao: cleanedDescription,
  };
}

function normalizeBill(bill: any) {
  return {
    ...bill,
    data_apresentacao: normalizeApiDateValue(bill?.data_apresentacao),
    data_ultima_acao: normalizeApiDateValue(bill?.data_ultima_acao),
    timeline: Array.isArray(bill?.timeline) ? bill.timeline.map(normalizeBillStage) : [],
    votacoes: Array.isArray(bill?.votacoes) ? bill.votacoes.map(normalizeVoteSession) : [],
    related_to_politician_as: Array.isArray(bill?.related_to_politician_as) ? bill.related_to_politician_as : [],
  };
}

function normalizePoliticianHistory(history: any) {
  return {
    ...history,
    timeline: Array.isArray(history?.timeline)
      ? history.timeline.map((item: any) => ({
          ...item,
          data: normalizeApiDateValue(item?.data),
        }))
      : [],
    voting_history: Array.isArray(history?.voting_history)
      ? history.voting_history.map((item: any) => ({
          ...item,
          data: normalizeApiDateValue(item?.data),
          resultado: formatVotingResult(item?.resultado),
        }))
      : [],
    approved_bills_related: Array.isArray(history?.approved_bills_related) ? history.approved_bills_related.map(normalizeBill) : [],
  };
}

export const apiClient = {
  getBills<T>(sort_by?: 'relevance') {
    const params = new URLSearchParams();
    if (sort_by) {
      params.set('sort_by', sort_by);
    }
    return request<T>(`/public/bills${params.toString() ? `?${params}` : ''}`, (payload) => (Array.isArray(payload) ? payload.map(normalizeBill) : []) as T);
  },
  getApprovedBills<T>(query?: string) {
    const params = new URLSearchParams();
    if (query) {
      params.set('query', query);
    }
    return request<T>(`/public/bills/approved${params.toString() ? `?${params}` : ''}`, (payload) => (Array.isArray(payload) ? payload.map(normalizeBill) : []) as T);
  },
  searchApprovedBills<T>(filters?: { theme?: string; author?: string; party?: string; year_from?: number; year_to?: number; page?: number; page_size?: number; sort_by?: 'relevance' | 'newest' | 'oldest' }) {
    const params = new URLSearchParams();
    if (filters?.theme) params.set('theme', filters.theme);
    if (filters?.author) params.set('author', filters.author);
    if (filters?.party) params.set('party', filters.party);
    if (typeof filters?.year_from === 'number') params.set('year_from', String(filters.year_from));
    if (typeof filters?.year_to === 'number') params.set('year_to', String(filters.year_to));
    if (typeof filters?.page === 'number') params.set('page', String(filters.page));
    if (typeof filters?.page_size === 'number') params.set('page_size', String(filters.page_size));
    if (filters?.sort_by) params.set('sort_by', filters.sort_by);
    return request<T>(`/public/bills/approved/search${params.toString() ? `?${params}` : ''}`, (payload) => normalizeApprovedBillsSearchResponse(payload) as T);
  },
  getApprovedBillFacets<T>() {
    return request<T>('/public/bills/approved/facets');
  },
  getBill<T>(billId: string | number) {
    return request<T>(`/public/bills/${billId}`, (payload) => normalizeBill(payload) as T);
  },
  getPoliticianHistory<T>(politicianId: string) {
    return request<T>(`/public/politicians/${politicianId}/history`, (payload) => normalizePoliticianHistory(payload) as T);
  },
  getPoliticians<T>(filters?: { query?: string; cargo?: string[]; partido?: string[]; uf?: string[]; cidade?: string[]; status_politico?: string[]; identidade_tipo?: string }) {
    const params = new URLSearchParams();
    if (filters?.query) params.set('query', filters.query);
    filters?.cargo?.forEach((value) => params.append('cargo', value));
    filters?.partido?.forEach((value) => params.append('partido', value));
    filters?.uf?.forEach((value) => params.append('uf', value));
    filters?.cidade?.forEach((value) => params.append('cidade', value));
    filters?.status_politico?.forEach((value) => params.append('status_politico', value));
    if (filters?.identidade_tipo) params.set('identidade_tipo', filters.identidade_tipo);
    return request<T>(`/public/politicians${params.toString() ? `?${params}` : ''}`);
  },
  getHighlights<T>() {
    return request<T>('/public/highlights');
  },
};
