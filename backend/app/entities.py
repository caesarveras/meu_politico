from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RawSourceRecordEntity(Base):
    __tablename__ = 'raw_source_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    request_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    request_params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    payload_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    collector_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    collected_at: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True, index=True)


class SyncRunEntity(Base):
    __tablename__ = 'sync_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True)
    checkpoint_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class DataIssueEntity(Base):
    __tablename__ = 'data_issues'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default='open')
    detected_at: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True, index=True)
    resolved_at: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True)


class PoliticianEntity(Base):
    __tablename__ = 'politicians'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_politician_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    partido: Mapped[str] = mapped_column(String(50), nullable=False)
    uf: Mapped[str] = mapped_column(String(10), nullable=False)
    cidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cargo: Mapped[str] = mapped_column(String(120), nullable=False)
    casa: Mapped[str] = mapped_column(String(120), nullable=False)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status_politico: Mapped[str] = mapped_column(String(50), default='ativo', nullable=False)
    identidade_tipo: Mapped[str] = mapped_column(String(30), default='atual', nullable=False, index=True)
    legislatura: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    mandato_inicio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mandato_fim: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fonte: Mapped[str] = mapped_column(String(50), default='seed', nullable=False)
    origem_externa_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    origem_dados: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ultima_sincronizacao: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True)


class BillEntity(Base):
    __tablename__ = 'bills'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sigla: Mapped[str] = mapped_column(String(20), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    ementa: Mapped[str] = mapped_column(Text, nullable=False)
    resumo: Mapped[str] = mapped_column(Text, nullable=False)
    autor_principal: Mapped[str] = mapped_column(String(255), nullable=False)
    casa_origem: Mapped[str] = mapped_column(String(120), nullable=False)
    status_atual: Mapped[str] = mapped_column(String(255), nullable=False)
    tema: Mapped[str] = mapped_column(String(255), nullable=False)
    impacto_financeiro: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    precisa_plenario: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aprovada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_apresentacao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_ultima_acao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timeline: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    votacoes: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    fonte: Mapped[str] = mapped_column(String(50), default='seed', nullable=False)
    origem_externa_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    origem_dados: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ultima_sincronizacao: Mapped[object | None] = mapped_column(DateTime(timezone=False), nullable=True)


class VoteEventEntity(Base):
    __tablename__ = 'vote_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    politician_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    politician_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bill_label: Mapped[str] = mapped_column(String(100), nullable=False)
    votacao_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data: Mapped[str | None] = mapped_column(String(50), nullable=True)
    orgao: Mapped[str] = mapped_column(String(255), nullable=False)
    resultado: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voto: Mapped[str] = mapped_column(String(50), nullable=False)
    partido: Mapped[str | None] = mapped_column(String(50), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fonte: Mapped[str] = mapped_column(String(50), default='seed', nullable=False)


class HighlightEntity(Base):
    __tablename__ = 'highlights'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
