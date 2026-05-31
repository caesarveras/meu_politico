export type BillStage = {
  ordem: number;
  fase: string;
  orgao: string;
  descricao: string;
  data: string | null;
  relator_id: number | null;
  relator_name: string | null;
  status: string;
};

export type VoteHistory = {
  bill_id: number | null;
  bill_label: string;
  bill_text: string | null;
  votacao_id: string | number | null;
  data: string | null;
  orgao: string;
  resultado: string | number | null;
  voto: string;
  fonte: string;
};

export type VoteRecord = {
  politician_id: number | null;
  politician_name: string;
  voto: string;
  partido: string | null;
  uf: string | null;
  cidade: string | null;
};

export type Bill = {
  id: number;
  sigla: string;
  numero: number;
  ano: number;
  ementa: string;
  resumo: string;
  autor_principal: string;
  casa_origem: string;
  status_atual: string;
  tema: string;
  impacto_financeiro: boolean;
  precisa_plenario: boolean;
  aprovada: boolean;
  data_apresentacao: string | null;
  data_ultima_acao: string | null;
  timeline: BillStage[];
  votacoes: Array<{ id: string | number; titulo: string; orgao: string; data: string; resultado: string | number | boolean; quorum: string; votos: VoteRecord[] }>;
  fonte: string;
  origem_externa_id: string | null;
  origem_dados: Record<string, unknown> | null;
  related_to_politician_as: string[];
  ultima_sincronizacao: string | null;
};

export type ApprovedBillFacets = {
  authors: string[];
  parties: string[];
  years: number[];
};

export type ApprovedBillsSearchResponse = {
  data: Bill[];
  meta: {
    count: number;
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
    schema: string;
  };
};

export type Politician = {
  id: number;
  canonical_politician_id?: number | null;
  nome: string;
  partido: string;
  uf: string;
  cidade: string | null;
  cargo: string;
  casa: string;
  foto_url: string | null;
  ativo: boolean;
  status_politico: string;
  identidade_tipo?: string;
  legislatura?: number | null;
  mandato_inicio?: string | null;
  mandato_fim?: string | null;
  fonte: string;
  origem_externa_id: string | null;
  origem_dados: Record<string, unknown> | null;
  ultima_sincronizacao: string | null;
};

export type PoliticianTimelineEvent = {
  ordem: number;
  data: string | null;
  titulo: string;
  descricao: string;
  tipo: string;
  fonte: string;
  legislatura: number | null;
  orgao: string | null;
};

export type PoliticianHistory = {
  politician: Politician;
  timeline: PoliticianTimelineEvent[];
  voting_history: VoteHistory[];
  approved_bills_related: Bill[];
};
