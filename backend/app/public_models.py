from pydantic import BaseModel, Field


class PublicTraceMetadata(BaseModel):
    source: str = "seed"
    source_reference: str | None = None
    last_synced_at: str | None = None
    confidence: str | None = None
    data_warnings: list[str] = Field(default_factory=list)


class PublicVoteRecord(BaseModel):
    politician_id: int | None = None
    politician_name: str
    voto: str
    partido: str | None = None
    uf: str | None = None
    cidade: str | None = None


class PublicVoteSession(BaseModel):
    id: str | int
    titulo: str
    orgao: str
    data: str
    resultado: str | int | bool
    quorum: str
    votos: list[PublicVoteRecord]


class PublicBillStage(BaseModel):
    ordem: int
    fase: str
    orgao: str
    descricao: str
    data: str | None = None
    relator_id: int | None = None
    relator_name: str | None = None
    status: str = "completed"


class PublicBillSummary(BaseModel):
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
    aprovada: bool = False
    data_apresentacao: str | None = None
    data_ultima_acao: str | None = None
    trace: PublicTraceMetadata


class PublicBillDetail(PublicBillSummary):
    impacto_financeiro: bool
    precisa_plenario: bool
    timeline: list[PublicBillStage]
    votacoes: list[PublicVoteSession]


class PublicPoliticianSummary(BaseModel):
    id: int
    nome: str
    partido: str
    uf: str
    cidade: str | None = None
    cargo: str
    casa: str
    foto_url: str | None = None
    ativo: bool = True
    status_politico: str = "ativo"
    trace: PublicTraceMetadata


class PublicPoliticianDetail(PublicPoliticianSummary):
    origem_externa_id: str | None = None
    origem_dados: dict | None = None


class PublicResponseEnvelope(BaseModel):
    data: object
    meta: dict[str, object] = Field(default_factory=dict)
