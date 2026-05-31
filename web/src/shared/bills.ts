import { Bill } from './types/api';

type BillOriginDetail = {
  uri?: string;
  statusProposicao?: {
    url?: string;
  };
};

const BODY_ACRONYM_LABELS: Record<string, string> = {
  PLEN: 'Plenário',
  CCJC: 'Comissão de Constituição e Justiça e de Cidadania',
  CFT: 'Comissão de Finanças e Tributação',
  CDE: 'Comissão de Desenvolvimento Econômico',
  CDEIC: 'Comissão de Desenvolvimento Econômico, Indústria, Comércio e Serviços',
  CCP: 'Órgão legislativo identificado pela sigla CCP',
  CE: 'Comissão de Educação',
  CCOM: 'Comissão de Comunicação',
  CCTCI: 'Comissão de Ciência, Tecnologia e Inovação',
  CCULT: 'Comissão de Cultura',
  CDC: 'Comissão de Defesa do Consumidor',
  CDU: 'Comissão de Desenvolvimento Urbano',
  CSSF: 'Comissão de Saúde',
  CTASP: 'Comissão de Trabalho',
  CMADS: 'Comissão de Meio Ambiente e Desenvolvimento Sustentável',
  MESA: 'Mesa Diretora',
  CFFC: 'Comissão de Fiscalização Financeira e Controle',
  CICS: 'Comissão de Indústria, Comércio e Serviços',
  CINDRA: 'Comissão de Integração Nacional e Desenvolvimento Regional',
  CLP: 'Comissão de Legislação Participativa',
  CME: 'Comissão de Minas e Energia',
  CPASF: 'Comissão de Previdência, Assistência Social, Infância, Adolescência e Família',
  CREDN: 'Comissão de Relações Exteriores e de Defesa Nacional',
  CSPCCO: 'Comissão de Segurança Pública e Combate ao Crime Organizado',
  CTUR: 'Comissão de Turismo',
  CVT: 'Comissão de Viação e Transportes',
};

const BODY_ACRONYM_HINTS: Record<string, string> = {
  PLEN: 'PLEN significa Plenário, que é o espaço em que o conjunto dos parlamentares delibera sobre a matéria.',
  MESA: 'MESA significa Mesa Diretora, órgão responsável por funções de direção e administração da Casa legislativa.',
  CCJC: 'CCJC significa Comissão de Constituição e Justiça e de Cidadania. Em geral, ela analisa aspectos constitucionais, jurídicos e de técnica legislativa da proposição.',
  CFT: 'CFT significa Comissão de Finanças e Tributação. Em geral, ela analisa impactos orçamentários e financeiros da proposta.',
  CE: 'CE significa Comissão de Educação, responsável por debater matérias relacionadas à política educacional.',
  CSSF: 'CSSF significa Comissão de Saúde, responsável por analisar matérias ligadas à saúde pública.',
  CTASP: 'CTASP significa Comissão de Trabalho, que discute matérias ligadas a trabalho, administração e serviço público.',
  CREDN: 'CREDN significa Comissão de Relações Exteriores e de Defesa Nacional, que trata de política externa e temas de defesa.',
  CSPCCO: 'CSPCCO significa Comissão de Segurança Pública e Combate ao Crime Organizado.',
  CDC: 'CDC significa Comissão de Defesa do Consumidor.',
  CDU: 'CDU significa Comissão de Desenvolvimento Urbano.',
  CME: 'CME significa Comissão de Minas e Energia.',
  CCOM: 'CCOM significa Comissão de Comunicação.',
  CTUR: 'CTUR significa Comissão de Turismo.',
  CVT: 'CVT significa Comissão de Viação e Transportes.',
};

const BILL_TYPE_LABELS: Record<string, string> = {
  PEC: 'Proposta de Emenda à Constituição',
  PL: 'Projeto de Lei',
  PLP: 'Projeto de Lei Complementar',
  PLC: 'Projeto de Lei da Câmara, classificação usada em certos fluxos legislativos entre as casas',
  PDC: 'Projeto de Decreto Legislativo',
  PDL: 'Projeto de Decreto Legislativo',
  PRC: 'Projeto de Resolução da Câmara',
  MPV: 'Medida Provisória',
  MSC: 'Mensagem',
  REQ: 'Requerimento',
};

const PRESIDENTIAL_TERMS = [
  { start: '1985-03-15', end: '1990-03-15', name: 'José Sarney', interim: false },
  { start: '1990-03-15', end: '1992-10-02', name: 'Fernando Collor de Mello', interim: false },
  { start: '1992-10-02', end: '1992-12-29', name: 'Itamar Franco', interim: true },
  { start: '1992-12-29', end: '1995-01-01', name: 'Itamar Franco', interim: false },
  { start: '1995-01-01', end: '2003-01-01', name: 'Fernando Henrique Cardoso', interim: false },
  { start: '2003-01-01', end: '2011-01-01', name: 'Luiz Inácio Lula da Silva', interim: false },
  { start: '2011-01-01', end: '2016-05-12', name: 'Dilma Rousseff', interim: false },
  { start: '2016-05-12', end: '2016-08-31', name: 'Michel Temer', interim: true },
  { start: '2016-08-31', end: '2019-01-01', name: 'Michel Temer', interim: false },
  { start: '2019-01-01', end: '2023-01-01', name: 'Jair Bolsonaro', interim: false },
  { start: '2023-01-01', end: '2100-01-01', name: 'Luiz Inácio Lula da Silva', interim: false },
];

export function formatVotingResult(result: string | number | boolean | null | undefined) {
  if (result === null || result === undefined || result === '') {
    return 'Resultado não informado';
  }

  const normalized = String(result).trim().toLowerCase();

  if (normalized === '1' || normalized === 'aprovado' || normalized === 'aprovada') {
    return 'Aprovado';
  }

  if (normalized === '0' || normalized === 'rejeitado' || normalized === 'rejeitada') {
    return 'Rejeitado';
  }

  return String(result);
}

export function getVotingResultTone(result: string | number | boolean | null | undefined) {
  const formatted = formatVotingResult(result).toLowerCase();
  if (formatted === 'aprovado') {
    return 'approved';
  }
  if (formatted === 'rejeitado') {
    return 'rejected';
  }
  return 'neutral';
}

export function describeBodyAcronym(acronym: string | null | undefined) {
  if (!acronym) {
    return 'Órgão não informado';
  }
  const normalized = acronym.trim().toUpperCase();
  const label = BODY_ACRONYM_LABELS[normalized];
  if (label) {
    return `${normalized} (${label})`;
  }
  if (/^[A-Z]{2,10}$/.test(normalized)) {
    return `${normalized} (sigla de órgão legislativo)`;
  }
  return acronym;
}

export function explainBodyAcronym(acronym: string | null | undefined) {
  if (!acronym) {
    return 'Órgão legislativo não informado.';
  }
  const normalized = acronym.trim().toUpperCase();
  const hint = BODY_ACRONYM_HINTS[normalized];
  if (hint) {
    return hint;
  }
  const label = BODY_ACRONYM_LABELS[normalized];
  if (label) {
    return `${normalized} significa ${label}.`;
  }
  if (/^[A-Z]{2,10}$/.test(normalized)) {
    return `${normalized} é a sigla de um órgão ou comissão legislativa exibida na tramitação.`;
  }
  return `${acronym} identifica o órgão legislativo exibido nesta etapa.`;
}

export function describeBillTypeAcronym(acronym: string | null | undefined) {
  if (!acronym) {
    return 'Tipo de proposição não informado';
  }
  const normalized = acronym.trim().toUpperCase();
  if (normalized === 'PLC') {
    return 'PLC significa Projeto de Lei da Câmara. Essa sigla costuma ser usada como classificação legislativa em certos fluxos entre as casas, e não deve ser confundida com PLP, que significa Projeto de Lei Complementar.';
  }
  if (normalized === 'PLP') {
    return 'PLP significa Projeto de Lei Complementar. Trata-se de uma proposição voltada a lei complementar, com regime jurídico próprio, e não deve ser confundida com PLC.';
  }
  if (normalized === 'PDC' || normalized === 'PDL') {
    return `${normalized} significa Projeto de Decreto Legislativo. A nomenclatura pode variar conforme a base ou o contexto legislativo, mas a sigla exibida é preservada como veio da fonte.`;
  }
  const label = BILL_TYPE_LABELS[normalized];
  if (label) {
    return `${normalized} significa ${label}.`;
  }
  if (/^[A-Z]{2,10}$/.test(normalized)) {
    return `${normalized} é a sigla do tipo de proposição legislativa exibida neste título.`;
  }
  return `${acronym} é o identificador do tipo de proposição exibido neste título.`;
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return 'Data não informada';
  }

  const normalizedValue = value.includes('T') ? value : value.replace(' ', 'T');
  const date = new Date(normalizedValue);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${day}/${month}/${year} às ${hours}:${minutes}`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return 'Data não informada';
  }

  const normalizedValue = value.includes('T') ? value : value.replace(' ', 'T');
  const date = new Date(normalizedValue);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

export function normalizeApiDateValue(value: unknown) {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmedValue = value.trim();
  if (!trimmedValue) {
    return null;
  }

  const normalizedValue = trimmedValue.includes('T') ? trimmedValue : trimmedValue.replace(' ', 'T');
  const date = new Date(normalizedValue);
  if (Number.isNaN(date.getTime())) {
    return trimmedValue;
  }

  return normalizedValue;
}

export function extractEmbeddedDateTime(text: string | null | undefined) {
  if (!text) {
    return null;
  }
  const match = text.match(/(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?)/);
  return match ? normalizeApiDateValue(match[1]) : null;
}

export function stripEmbeddedDateTime(text: string | null | undefined) {
  if (!text) {
    return '';
  }
  return text.replace(/\s*em\s*\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?\.?/i, '.').replace(/\.\./g, '.').trim();
}

export function getPresidentInOffice(value: string | null | undefined) {
  if (!value) {
    return null;
  }
  const normalizedValue = value.includes('T') ? value : value.replace(' ', 'T');
  const date = new Date(normalizedValue);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const match = PRESIDENTIAL_TERMS.find((term) => {
    const start = new Date(`${term.start}T00:00:00`);
    const end = new Date(`${term.end}T00:00:00`);
    return date >= start && date < end;
  });

  if (!match) {
    return null;
  }

  return match.interim ? `${match.name} (interino)` : match.name;
}

export function getBillStageTone(fase: string | null | undefined, descricao: string | null | undefined) {
  const text = `${fase ?? ''} ${descricao ?? ''}`.toLowerCase();
  if (text.includes('veto') || text.includes('rejeitad')) {
    return 'rejected';
  }
  if (text.includes('sanç') || text.includes('sanc') || text.includes('promulg') || text.includes('aprovad')) {
    return 'approved';
  }
  return 'neutral';
}

export function describeBillStage(fase: string | null | undefined, descricao: string | null | undefined) {
  const normalizedFase = (fase ?? '').trim().toLowerCase();
  const text = `${fase ?? ''} ${descricao ?? ''}`.toLowerCase();

  if (!normalizedFase && !text.trim()) {
    return 'Etapa legislativa não informada.';
  }
  if (text.includes('apresent')) {
    return 'Indica a apresentação formal da proposição no processo legislativo.';
  }
  if (text.includes('relator')) {
    return 'Indica a etapa em que houve designação ou atuação de relatoria sobre a matéria.';
  }
  if (text.includes('parecer')) {
    return 'Indica que houve parecer, ou seja, uma manifestação técnica ou política sobre a proposta.';
  }
  if (text.includes('aprovad')) {
    return 'Indica uma etapa de aprovação da matéria em algum órgão ou fase do processo legislativo.';
  }
  if (text.includes('rejeitad')) {
    return 'Indica uma etapa em que a matéria foi rejeitada em algum órgão ou fase do processo legislativo.';
  }
  if (text.includes('veto')) {
    return 'Indica etapa relacionada a veto presidencial, total ou parcial, sobre o texto aprovado pelo Legislativo.';
  }
  if (text.includes('sanç') || text.includes('sanc')) {
    return 'Indica etapa de sanção presidencial da matéria aprovada pelo Legislativo.';
  }
  if (text.includes('promulg')) {
    return 'Indica a promulgação da norma, etapa em que o ato é formalmente declarado válido para publicação e vigência.';
  }
  if (text.includes('arquiv')) {
    return 'Indica arquivamento da matéria, isto é, interrupção da tramitação sem conversão em norma naquele momento.';
  }
  return `Etapa registrada como ${fase ?? 'fase não informada'} no processo legislativo.`;
}

export function getOfficialBillUrl(bill: Pick<Bill, 'id' | 'origem_dados'>) {
  const sourceData = bill.origem_dados as { detalhe?: BillOriginDetail } | null;
  const detail = sourceData?.detalhe;
  const status = detail?.statusProposicao;

  if (typeof status?.url === 'string' && status.url.length > 0) {
    return status.url;
  }

  if (typeof detail?.uri === 'string' && detail.uri.length > 0) {
    return detail.uri;
  }

  return `https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=${bill.id}`;
}
