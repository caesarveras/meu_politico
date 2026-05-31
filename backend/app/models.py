from pydantic import BaseModel, Field


class Politician(BaseModel):
    id: int
    canonical_politician_id: int | None = None
    nome: str
    partido: str
    uf: str
    cidade: str | None = None
    cargo: str
    casa: str
    foto_url: str | None = None
    ativo: bool = True
    status_politico: str = "ativo"
    identidade_tipo: str = "atual"
    legislatura: int | None = None
    mandato_inicio: str | None = None
    mandato_fim: str | None = None
    fonte: str = "seed"
    origem_externa_id: str | None = None
    origem_dados: dict | None = None
    ultima_sincronizacao: str | None = None


class BillStage(BaseModel):
    ordem: int
    fase: str
    orgao: str
    descricao: str
    data: str | None = None
    relator_id: int | None = None
    relator_name: str | None = None
    status: str = Field(default="completed")


class VoteRecord(BaseModel):
    politician_id: int | None = None
    politician_name: str
    voto: str
    partido: str | None = None
    uf: str | None = None
    cidade: str | None = None


class VoteSession(BaseModel):
    id: str | int
    titulo: str
    orgao: str
    data: str
    resultado: str | int | bool
    quorum: str
    votos: list[VoteRecord]


class PoliticianTimelineEvent(BaseModel):
    ordem: int
    data: str | None = None
    titulo: str
    descricao: str
    tipo: str
    fonte: str = "seed"
    legislatura: int | None = None
    orgao: str | None = None


class PoliticianVoteHistory(BaseModel):
    bill_id: int | None = None
    bill_label: str
    bill_text: str | None = None
    votacao_id: str | int | None = None
    data: str | None = None
    orgao: str
    resultado: str | None = None
    voto: str
    fonte: str = "seed"


class Bill(BaseModel):
    id: int
    sigla: str
    numero: int
    ano: int
    ementa: str
    resumo: str
    autor_principal: str
    casa_origem: str
    status_atual: str
    tema: str
    impacto_financeiro: bool
    precisa_plenario: bool
    aprovada: bool = False
    data_apresentacao: str | None = None
    data_ultima_acao: str | None = None
    timeline: list[BillStage]
    votacoes: list[VoteSession]
    fonte: str = "seed"
    origem_externa_id: str | None = None
    origem_dados: dict | None = None
    related_to_politician_as: list[str] = []
    ultima_sincronizacao: str | None = None


class PoliticianHistory(BaseModel):
    politician: Politician
    timeline: list[PoliticianTimelineEvent] = []
    voting_history: list[PoliticianVoteHistory]
    approved_bills_related: list[Bill]


class Highlight(BaseModel):
    title: str
    subtitle: str
    metric: str


class SyncRunSummary(BaseModel):
    id: int
    source: str
    sync_type: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    processed_count: int
    error_count: int
    checkpoint_json: dict | None = None
    metadata_json: dict | None = None


class DataIssueSummary(BaseModel):
    id: int
    issue_type: str
    source: str
    entity_type: str
    entity_id: str | None = None
    severity: str
    description: str
    status: str
    detected_at: str | None = None


class SyncStatusSummary(BaseModel):
    last_run_at: str | None = None
    latest_run: SyncRunSummary | None = None
    open_issues_count: int
    recent_issues: list[DataIssueSummary]
    raw_records_count: int


class HistoricalCheckpointSummary(BaseModel):
    requested_start_year: int | None = None
    effective_start_year: int | None = None
    last_completed_year: int | None = None
    end_year: int | None = None
    resume: bool | None = None
    imported_bills: int = 0
    updated_bills: int = 0
    imported_politicians: int = 0
    updated_politicians: int = 0
    source_errors: int = 0


class HistoricalCoverageSummary(BaseModel):
    requested_start_year: int | None = None
    effective_start_year: int | None = None
    last_completed_year: int | None = None
    end_year: int | None = None
    canonical_politicians_count: int = 0
    historical_politician_snapshots_count: int = 0
    legislatures_covered_count: int = 0
    earliest_legislature: int | None = None
    latest_legislature: int | None = None
    bills_count: int = 0
    approved_bills_count: int = 0
    earliest_bill_year: int | None = None
    latest_bill_year: int | None = None
    open_data_issues_count: int = 0
    latest_checkpoint: dict | None = None
    bills_by_year: dict[str, int] = {}
    bills_by_type: dict[str, int] = {}
    approved_bills_by_type: dict[str, int] = {}
    bills_by_year_and_type: dict[str, dict[str, int]] = {}
    expected_legislatures: list[int] = []
    missing_bill_years: list[int] = []
    missing_bill_years_api_failure: list[int] = []
    missing_bill_years_official_unavailable: list[int] = []
    missing_legislatures: list[int] = []
    missing_important_type_years: dict[str, list[int]] = {}
    low_volume_type_years: dict[str, list[int]] = {}
    coverage_warnings: list[str] = []
