import asyncio
from datetime import datetime
import hashlib

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.entities import BillEntity, DataIssueEntity, PoliticianEntity, RawSourceRecordEntity, SyncRunEntity, VoteEventEntity
from app.models import DataIssueSummary, HistoricalCheckpointSummary, HistoricalCoverageSummary, SyncRunSummary, SyncStatusSummary
from app.services.job_lock import job_lock_service
from app.services.sync_collector import sync_collector
from app.services.sync_normalizer import sync_normalizer

class SyncService:
    def __init__(self) -> None:
        self.last_run_at: datetime | None = None

    @staticmethod
    def _chunk_list(items: list[dict], chunk_size: int) -> list[list[dict]]:
        size = max(1, chunk_size)
        return [items[index:index + size] for index in range(0, len(items), size)]

    @staticmethod
    def _extract_proposition_id(proposicao: dict) -> int | None:
        value = proposicao.get("id")
        return int(value) if isinstance(value, int) else int(value) if isinstance(value, str) and value.isdigit() else None

    async def _fetch_proposition_bundle(self, proposicao_resumo: dict) -> dict:
        proposicao_id = self._extract_proposition_id(proposicao_resumo)
        if proposicao_id is None:
            return {"resumo": proposicao_resumo, "skip": True}

        try:
            detalhe, tramitacoes, votacoes = await asyncio.gather(
                sync_collector.fetch_proposicao(proposicao_id),
                sync_collector.fetch_tramitacoes(proposicao_id),
                sync_collector.fetch_votacoes(proposicao_id),
            )
            return {
                "resumo": proposicao_resumo,
                "detalhe": detalhe,
                "tramitacoes": tramitacoes,
                "votacoes": votacoes,
                "skip": False,
            }
        except httpx.HTTPError as exc:
            return {
                "resumo": proposicao_resumo,
                "error": exc,
                "skip": False,
            }

    async def _fetch_proposition_bundles(self, proposicoes: list[dict], max_concurrency: int) -> list[dict]:
        semaphore = asyncio.Semaphore(max(1, max_concurrency))

        async def runner(item: dict) -> dict:
            async with semaphore:
                return await self._fetch_proposition_bundle(item)

        return await asyncio.gather(*(runner(item) for item in proposicoes))

    @staticmethod
    def _start_sync_run(db: Session, source: str, sync_type: str, metadata: dict | None = None) -> SyncRunEntity:
        sync_run = SyncRunEntity(
            source=source,
            sync_type=sync_type,
            status="running",
            started_at=datetime.utcnow(),
            processed_count=0,
            error_count=0,
            metadata_json=metadata,
        )
        db.add(sync_run)
        db.flush()
        return sync_run

    @staticmethod
    def _finish_sync_run(
        sync_run: SyncRunEntity,
        *,
        status: str,
        processed_count: int,
        error_count: int,
        checkpoint: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        sync_run.status = status
        sync_run.finished_at = datetime.utcnow()
        sync_run.processed_count = processed_count
        sync_run.error_count = error_count
        sync_run.checkpoint_json = checkpoint
        sync_run.metadata_json = metadata

    @staticmethod
    def _build_source_key(source: str, external_id: int | str) -> str:
        return f"{source}:{external_id}"

    def _build_timeline(self, tramitacoes: list[dict], status_proposicao: dict) -> list[dict]:
        return sync_normalizer.build_timeline(tramitacoes, status_proposicao)

    @staticmethod
    def _build_payload_hash(payload: dict) -> str:
        return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()

    def _record_raw_payload(self, db: Session, path: str, url: str, params: dict | None, payload: dict) -> None:
        cleaned_path = path.strip("/")
        resource = cleaned_path.replace("/", ".") or "root"
        path_parts = [part for part in cleaned_path.split("/") if part]
        external_id = None
        if path_parts:
            last_part = path_parts[-1]
            if last_part != "dados" and last_part not in {"deputados", "proposicoes", "tramitacoes", "votacoes", "votos", "historico", "eventos", "mandatosExternos"}:
                external_id = last_part
            elif len(path_parts) >= 2 and path_parts[-2].isdigit():
                external_id = path_parts[-2]

        db.add(
            RawSourceRecordEntity(
                source="camara",
                resource=resource,
                external_id=external_id,
                request_url=url,
                request_params_json=params,
                payload_json=payload,
                payload_hash=self._build_payload_hash(payload),
                collector_version=settings.app_version,
                collected_at=datetime.utcnow(),
            )
        )

    @staticmethod
    def _update_historical_checkpoint(
        sync_run: SyncRunEntity,
        *,
        requested_start_year: int,
        effective_start_year: int,
        end_year: int,
        resume: bool,
        imported_bills: int,
        updated_bills: int,
        imported_politicians: int,
        updated_politicians: int,
        source_errors: int,
        phase: str,
        last_completed_year: int | None = None,
        last_completed_month: int | None = None,
        last_completed_batch: int | None = None,
        current_deputy_index: int | None = None,
        total_historical_deputies: int | None = None,
        current_deputy_id: int | None = None,
    ) -> None:
        sync_run.checkpoint_json = {
            "requested_start_year": requested_start_year,
            "effective_start_year": effective_start_year,
            "last_completed_year": last_completed_year,
            "last_completed_month": last_completed_month,
            "last_completed_batch": last_completed_batch,
            "end_year": end_year,
            "resume": resume,
            "phase": phase,
            "current_deputy_index": current_deputy_index,
            "total_historical_deputies": total_historical_deputies,
            "current_deputy_id": current_deputy_id,
            "imported_bills": imported_bills,
            "updated_bills": updated_bills,
            "imported_politicians": imported_politicians,
            "updated_politicians": updated_politicians,
            "source_errors": source_errors,
        }

    def _record_data_issue(
        self,
        db: Session,
        *,
        issue_type: str,
        entity_type: str,
        description: str,
        entity_id: str | None = None,
        severity: str = "warning",
        status: str = "open",
    ) -> None:
        existing_issue = (
            db.query(DataIssueEntity)
            .filter(
                DataIssueEntity.issue_type == issue_type,
                DataIssueEntity.source == "camara",
                DataIssueEntity.entity_type == entity_type,
                DataIssueEntity.entity_id == entity_id,
                DataIssueEntity.severity == severity,
                DataIssueEntity.description == description,
                DataIssueEntity.status == "open",
            )
            .order_by(DataIssueEntity.id.desc())
            .first()
        )
        if existing_issue is not None:
            return

        db.add(
            DataIssueEntity(
                issue_type=issue_type,
                source="camara",
                entity_type=entity_type,
                entity_id=entity_id,
                severity=severity,
                description=description,
                status=status,
                detected_at=datetime.utcnow(),
            )
        )

    def list_data_issues(
        self,
        db: Session,
        *,
        status: str | None = None,
        severity: str | None = None,
        issue_type: str | None = None,
        limit: int = 50,
    ) -> list[DataIssueSummary]:
        statement = db.query(DataIssueEntity)
        if status:
            statement = statement.filter(DataIssueEntity.status == status)
        if severity:
            statement = statement.filter(DataIssueEntity.severity == severity)
        if issue_type:
            statement = statement.filter(DataIssueEntity.issue_type == issue_type)

        rows = (
            statement
            .order_by(DataIssueEntity.detected_at.desc(), DataIssueEntity.id.desc())
            .limit(max(1, min(limit, 200)))
            .all()
        )
        return [
            DataIssueSummary(
                id=row.id,
                issue_type=row.issue_type,
                source=row.source,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                severity=row.severity,
                description=row.description,
                status=row.status,
                detected_at=row.detected_at.isoformat() + "Z" if row.detected_at else None,
            )
            for row in rows
        ]

    def _resolve_data_issues(
        self,
        db: Session,
        *,
        issue_types: list[str],
        entity_type: str,
        entity_id: str | None = None,
    ) -> None:
        rows = db.query(DataIssueEntity).filter(
            DataIssueEntity.source == "camara",
            DataIssueEntity.entity_type == entity_type,
            DataIssueEntity.status == "open",
            DataIssueEntity.issue_type.in_(issue_types),
        )
        if entity_id is None:
            rows = rows.filter(DataIssueEntity.entity_id.is_(None))
        else:
            rows = rows.filter(DataIssueEntity.entity_id == entity_id)

        for row in rows.all():
            row.status = "resolved"
            row.resolved_at = datetime.utcnow()

    def get_sync_status(self, db: Session) -> SyncStatusSummary:
        latest_run_row = (
            db.query(SyncRunEntity)
            .order_by(SyncRunEntity.started_at.desc(), SyncRunEntity.id.desc())
            .first()
        )
        recent_issue_rows = (
            db.query(DataIssueEntity)
            .order_by(DataIssueEntity.detected_at.desc(), DataIssueEntity.id.desc())
            .limit(10)
            .all()
        )
        open_issues_count = db.query(func.count(DataIssueEntity.id)).filter(DataIssueEntity.status == "open").scalar() or 0
        raw_records_count = db.query(func.count(RawSourceRecordEntity.id)).scalar() or 0

        latest_run = None
        if latest_run_row is not None:
            latest_run = SyncRunSummary(
                id=latest_run_row.id,
                source=latest_run_row.source,
                sync_type=latest_run_row.sync_type,
                status=latest_run_row.status,
                started_at=latest_run_row.started_at.isoformat() + "Z" if latest_run_row.started_at else None,
                finished_at=latest_run_row.finished_at.isoformat() + "Z" if latest_run_row.finished_at else None,
                processed_count=latest_run_row.processed_count,
                error_count=latest_run_row.error_count,
                checkpoint_json=latest_run_row.checkpoint_json,
                metadata_json=latest_run_row.metadata_json,
            )

        recent_issues = [
            DataIssueSummary(
                id=row.id,
                issue_type=row.issue_type,
                source=row.source,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                severity=row.severity,
                description=row.description,
                status=row.status,
                detected_at=row.detected_at.isoformat() + "Z" if row.detected_at else None,
            )
            for row in recent_issue_rows
        ]

        return SyncStatusSummary(
            last_run_at=self.last_run_at.isoformat() + "Z" if self.last_run_at else None,
            latest_run=latest_run,
            open_issues_count=int(open_issues_count),
            recent_issues=recent_issues,
            raw_records_count=int(raw_records_count),
        )

    @staticmethod
    def _get_last_historical_checkpoint(db: Session) -> dict | None:
        latest_run = (
            db.query(SyncRunEntity)
            .filter(SyncRunEntity.source == "camara", SyncRunEntity.sync_type == "historical_backfill")
            .order_by(SyncRunEntity.started_at.desc(), SyncRunEntity.id.desc())
            .first()
        )
        if latest_run is None or not isinstance(latest_run.checkpoint_json, dict):
            return None
        return latest_run.checkpoint_json

    def get_last_historical_checkpoint(self, db: Session) -> HistoricalCheckpointSummary:
        checkpoint = self._get_last_historical_checkpoint(db) or {}
        return HistoricalCheckpointSummary(
            requested_start_year=checkpoint.get("requested_start_year"),
            effective_start_year=checkpoint.get("effective_start_year"),
            last_completed_year=checkpoint.get("last_completed_year"),
            end_year=checkpoint.get("end_year"),
            resume=checkpoint.get("resume"),
            imported_bills=checkpoint.get("imported_bills") or 0,
            updated_bills=checkpoint.get("updated_bills") or 0,
            imported_politicians=checkpoint.get("imported_politicians") or 0,
            updated_politicians=checkpoint.get("updated_politicians") or 0,
            source_errors=checkpoint.get("source_errors") or 0,
        )

    async def get_historical_coverage(self, db: Session) -> HistoricalCoverageSummary:
        checkpoint = self._get_last_historical_checkpoint(db) or {}
        requested_start_year = checkpoint.get("requested_start_year")
        effective_start_year = checkpoint.get("effective_start_year")
        last_completed_year = checkpoint.get("last_completed_year")
        end_year = checkpoint.get("end_year")

        canonical_statement = db.query(PoliticianEntity).filter(PoliticianEntity.identidade_tipo != "historica")
        historical_statement = db.query(PoliticianEntity).filter(PoliticianEntity.identidade_tipo == "historica")
        bill_statement = db.query(BillEntity)

        if db.query(PoliticianEntity).filter(PoliticianEntity.fonte != "seed").count() > 0:
            canonical_statement = canonical_statement.filter(PoliticianEntity.fonte != "seed")
            historical_statement = historical_statement.filter(PoliticianEntity.fonte != "seed")
        if db.query(BillEntity).filter(BillEntity.fonte != "seed").count() > 0:
            bill_statement = bill_statement.filter(BillEntity.fonte != "seed")

        canonical_politicians_count = canonical_statement.count()
        historical_politician_snapshots_count = historical_statement.count()

        legislaturas = [
            value
            for (value,) in historical_statement.with_entities(PoliticianEntity.legislatura).distinct().all()
            if isinstance(value, int)
        ]

        bill_rows = bill_statement.with_entities(BillEntity.ano, BillEntity.aprovada, BillEntity.sigla).all()
        bills_by_year: dict[str, int] = {}
        bills_by_type: dict[str, int] = {}
        approved_bills_by_type: dict[str, int] = {}
        bills_by_year_and_type: dict[str, dict[str, int]] = {}
        approved_bills_count = 0
        bill_years: list[int] = []
        for ano, aprovada, sigla in bill_rows:
            year_key = str(ano) if isinstance(ano, int) else "N/A"
            if year_key not in bills_by_year_and_type:
                bills_by_year_and_type[year_key] = {}
            if isinstance(ano, int):
                bills_by_year[str(ano)] = bills_by_year.get(str(ano), 0) + 1
                bill_years.append(ano)
            bill_type = sigla.strip().upper() if isinstance(sigla, str) and sigla.strip() else "N/A"
            bills_by_type[bill_type] = bills_by_type.get(bill_type, 0) + 1
            bills_by_year_and_type[year_key][bill_type] = bills_by_year_and_type[year_key].get(bill_type, 0) + 1
            if aprovada:
                approved_bills_count += 1
                approved_bills_by_type[bill_type] = approved_bills_by_type.get(bill_type, 0) + 1

        open_data_issues_count = db.query(func.count(DataIssueEntity.id)).filter(DataIssueEntity.status == "open").scalar() or 0
        missing_bill_years: list[int] = []
        missing_bill_years_api_failure: list[int] = []
        missing_bill_years_official_unavailable: list[int] = []
        coverage_warnings: list[str] = []
        if isinstance(effective_start_year, int) and isinstance(end_year, int) and effective_start_year <= end_year:
            loaded_bill_years = set(bill_years)
            missing_bill_years = [year for year in range(effective_start_year, end_year + 1) if year not in loaded_bill_years]
            failed_bill_batch_years = {
                int(entity_id)
                for (entity_id,) in db.query(DataIssueEntity.entity_id)
                .filter(
                    DataIssueEntity.status == "open",
                    DataIssueEntity.issue_type == "source_fetch_error",
                    DataIssueEntity.entity_type == "bill_batch",
                    DataIssueEntity.entity_id.is_not(None),
                )
                .all()
                if isinstance(entity_id, str) and entity_id.isdigit()
            }
            missing_bill_years_api_failure = [year for year in missing_bill_years if year in failed_bill_batch_years]
            missing_bill_years_official_unavailable = [year for year in missing_bill_years if year not in failed_bill_batch_years]
            if missing_bill_years:
                coverage_warnings.append(
                    "Existem anos sem proposições carregadas no intervalo esperado do backfill histórico."
                )
            if missing_bill_years_api_failure:
                coverage_warnings.append(
                    "Existem anos sem dado por falha na API durante o backfill histórico."
                )
            if missing_bill_years_official_unavailable:
                coverage_warnings.append(
                    "Existem anos sem arquivo/disponibilidade oficial identificado para o backfill histórico."
                )

        try:
            official_legislatures = await sync_collector.fetch_legislaturas()
        except httpx.HTTPError:
            official_legislatures = []
            coverage_warnings.append(
                "Não foi possível consultar a lista oficial de legislaturas da Câmara para validar a cobertura histórica neste momento."
            )
        expected_legislatures: list[int] = []
        reference_start_year = effective_start_year if isinstance(effective_start_year, int) else requested_start_year
        reference_end_year = end_year if isinstance(end_year, int) else last_completed_year
        for item in official_legislatures:
            legislatura_id = self._safe_int(item.get("id"))
            election_year = self._safe_int(item.get("anoEleicao"))
            if legislatura_id is None:
                continue
            if election_year is not None:
                if isinstance(reference_start_year, int) and election_year < reference_start_year - 2:
                    continue
                if isinstance(reference_end_year, int) and election_year > reference_end_year:
                    continue
            expected_legislatures.append(legislatura_id)
        expected_legislatures = sorted(set(expected_legislatures))
        loaded_legislatures = set(legislaturas)
        missing_legislatures = [legislatura for legislatura in expected_legislatures if legislatura not in loaded_legislatures]

        important_types = ["PL", "PLP", "PEC", "MPV"]
        missing_important_type_years: dict[str, list[int]] = {}
        low_volume_type_years: dict[str, list[int]] = {}
        if isinstance(effective_start_year, int) and isinstance(end_year, int) and effective_start_year <= end_year:
            expected_years = list(range(effective_start_year, end_year + 1))
            for bill_type in important_types:
                yearly_counts = [
                    bills_by_year_and_type.get(str(year), {}).get(bill_type, 0)
                    for year in expected_years
                ]
                if not any(yearly_counts):
                    continue

                missing_years_for_type = [
                    year
                    for year in expected_years
                    if bills_by_year_and_type.get(str(year), {}).get(bill_type, 0) == 0
                ]
                if missing_years_for_type:
                    missing_important_type_years[bill_type] = missing_years_for_type

                positive_counts = [count for count in yearly_counts if count > 0]
                if len(positive_counts) < 3:
                    continue
                average_count = sum(positive_counts) / len(positive_counts)
                low_volume_threshold = max(1, average_count * 0.3)
                low_volume_years_for_type = [
                    year
                    for year in expected_years
                    if 0 < bills_by_year_and_type.get(str(year), {}).get(bill_type, 0) < low_volume_threshold
                ]
                if low_volume_years_for_type:
                    low_volume_type_years[bill_type] = low_volume_years_for_type

        if historical_politician_snapshots_count == 0:
            coverage_warnings.append("Nenhum snapshot histórico de parlamentar foi encontrado na base.")
        elif missing_legislatures:
            coverage_warnings.append("Existem legislaturas oficiais da Câmara sem snapshots históricos de parlamentares na base.")

        if canonical_politicians_count == 0:
            coverage_warnings.append("Nenhum parlamentar canônico foi encontrado na base sincronizada.")
        if len(bill_rows) == 0:
            coverage_warnings.append("Nenhuma proposição histórica foi encontrada na base sincronizada.")
        if int(open_data_issues_count) > 0:
            coverage_warnings.append("Há issues abertas de dados que podem indicar cobertura incompleta ou falhas de origem.")
        if missing_important_type_years:
            coverage_warnings.append("Existem tipos importantes ausentes em anos específicos dentro do recorte histórico.")
        if low_volume_type_years:
            coverage_warnings.append("Existem tipos importantes com volume muito abaixo do padrão histórico em anos específicos.")

        return HistoricalCoverageSummary(
            requested_start_year=requested_start_year,
            effective_start_year=effective_start_year,
            last_completed_year=last_completed_year,
            end_year=end_year,
            canonical_politicians_count=canonical_politicians_count,
            historical_politician_snapshots_count=historical_politician_snapshots_count,
            legislatures_covered_count=len(legislaturas),
            earliest_legislature=min(legislaturas) if legislaturas else None,
            latest_legislature=max(legislaturas) if legislaturas else None,
            bills_count=len(bill_rows),
            approved_bills_count=approved_bills_count,
            earliest_bill_year=min(bill_years) if bill_years else None,
            latest_bill_year=max(bill_years) if bill_years else None,
            open_data_issues_count=int(open_data_issues_count),
            latest_checkpoint=checkpoint,
            bills_by_year=dict(sorted(bills_by_year.items(), key=lambda item: int(item[0]))),
            bills_by_type=dict(sorted(bills_by_type.items(), key=lambda item: (-item[1], item[0]))),
            approved_bills_by_type=dict(sorted(approved_bills_by_type.items(), key=lambda item: (-item[1], item[0]))),
            bills_by_year_and_type={
                year: dict(sorted(types.items(), key=lambda item: (-item[1], item[0])))
                for year, types in sorted(
                    bills_by_year_and_type.items(),
                    key=lambda item: (999999 if item[0] == "N/A" else int(item[0]))
                )
            },
            expected_legislatures=expected_legislatures,
            missing_bill_years=missing_bill_years,
            missing_bill_years_api_failure=missing_bill_years_api_failure,
            missing_bill_years_official_unavailable=missing_bill_years_official_unavailable,
            missing_legislatures=missing_legislatures,
            missing_important_type_years=missing_important_type_years,
            low_volume_type_years=low_volume_type_years,
            coverage_warnings=coverage_warnings,
        )

    async def _populate_votes_for_sessions(self, sessions: list[dict]) -> list[dict]:
        async def fetch_votes(session: dict) -> dict:
            session_id = session.get("id")
            votes: list[dict] = []
            if session_id:
                try:
                    votes = sync_normalizer.normalize_vote_records(await sync_collector.fetch_votacao_votos(session_id))
                except httpx.HTTPError:
                    votes = []
            return {**session, "votos": votes}

        return await asyncio.gather(*(fetch_votes(session) for session in sessions)) if sessions else []

    @staticmethod
    def _normalize_politician_status(deputado: dict, detalhe: dict | None = None) -> tuple[bool, str]:
        payloads = [payload for payload in [detalhe or {}, deputado] if payload]
        raw_values: list[str] = []
        for payload in payloads:
            ultimo_status = payload.get("ultimoStatus") or {}
            raw_values.extend(
                [
                    str(ultimo_status.get("situacao") or "").strip(),
                    str(ultimo_status.get("descricaoStatus") or "").strip(),
                    str(payload.get("situacao") or "").strip(),
                    str(payload.get("descricaoStatus") or "").strip(),
                    str(payload.get("condicaoEleitoral") or "").strip(),
                ]
            )

        text = " ".join(value.lower() for value in raw_values if value)
        if not text:
            ativo = bool((detalhe or {}).get("ultimoStatus") or deputado.get("uri"))
            return ativo, "ativo" if ativo else "desligado"
        if "cass" in text or "perda de mandato por resolução" in text or "perda de mandato" in text:
            return False, "cassado"
        if "suplente" in text:
            return True, "ativo"
        if "exerc" in text or "titular" in text or "ativo" in text:
            return True, "ativo"
        return False, "desligado"

    def _store_vote_events(self, db: Session, bill_id: int, bill_label: str, vote_sessions: list[dict], source: str) -> None:
        db.query(VoteEventEntity).filter(VoteEventEntity.bill_id == bill_id, VoteEventEntity.fonte == source).delete()
        for session in vote_sessions:
            for vote in session.get("votos", []):
                db.add(
                    VoteEventEntity(
                        politician_id=vote.get("politician_id"),
                        politician_name=vote.get("politician_name", "Parlamentar não informado"),
                        bill_id=bill_id,
                        bill_label=bill_label,
                        votacao_id=session.get("id"),
                        data=session.get("data"),
                        orgao=session.get("orgao", "Órgão não informado"),
                        resultado=session.get("resultado"),
                        voto=vote.get("voto", "Não informado"),
                        partido=vote.get("partido"),
                        uf=vote.get("uf"),
                        fonte=source,
                    )
                )

    @staticmethod
    def _safe_int(value) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _build_historical_politician_snapshot_id(self, canonical_id: int, legislatura: int | None, year_hint: int | None = None) -> int:
        suffix = legislatura if legislatura is not None else (year_hint or 0)
        return canonical_id * 1000 + suffix

    def _upsert_historical_politician_snapshot(
        self,
        db: Session,
        *,
        canonical_id: int,
        nome: str,
        partido: str,
        uf: str,
        cidade: str | None,
        legislatura: int | None,
        mandato_inicio: str | None,
        mandato_fim: str | None,
        origem_externa_id: str,
        origem_dados: dict,
        sync_started_at: datetime,
    ) -> tuple[bool, bool]:
        snapshot_id = self._build_historical_politician_snapshot_id(canonical_id, legislatura)
        entity = db.query(PoliticianEntity).filter(PoliticianEntity.origem_externa_id == origem_externa_id).one_or_none()
        if entity is None:
            entity = db.get(PoliticianEntity, snapshot_id)

        payload = {
            "canonical_politician_id": canonical_id,
            "nome": nome,
            "partido": partido or "N/A",
            "uf": uf or "BR",
            "cidade": cidade,
            "cargo": "Deputado Federal",
            "casa": "Câmara dos Deputados",
            "foto_url": None,
            "ativo": False,
            "status_politico": "historico",
            "identidade_tipo": "historica",
            "legislatura": legislatura,
            "mandato_inicio": mandato_inicio,
            "mandato_fim": mandato_fim,
            "fonte": "camara",
            "origem_externa_id": origem_externa_id,
            "origem_dados": origem_dados,
            "ultima_sincronizacao": sync_started_at,
        }

        if entity is None:
            db.add(PoliticianEntity(id=snapshot_id, **payload))
            return True, False

        for field, value in payload.items():
            setattr(entity, field, value)
        return False, True

    async def _sync_historical_politicians_backfill(
        self,
        db: Session,
        sync_started_at: datetime,
        *,
        sync_run: SyncRunEntity,
        requested_start_year: int,
        effective_start_year: int,
        end_year: int,
        resume: bool,
        imported_bills: int,
        updated_bills: int,
        source_errors: int,
    ) -> tuple[int, int]:
        imported = 0
        updated = 0
        try:
            deputados_historicos = await sync_collector.fetch_deputados_historicos()
        except httpx.HTTPError:
            self._record_data_issue(
                db,
                issue_type="source_fetch_error",
                entity_type="politician_batch",
                severity="error",
                description="Falha ao buscar deputados históricos da Câmara durante o backfill histórico.",
            )
            return imported, updated

        try:
            legislaturas = await sync_collector.fetch_legislaturas()
        except httpx.HTTPError:
            self._record_data_issue(
                db,
                issue_type="source_fetch_error",
                entity_type="legislature_batch",
                severity="error",
                description="Falha ao buscar legislaturas da Câmara durante o backfill histórico de parlamentares.",
            )
            legislaturas = []

        legislaturas_validas = []
        for item in legislaturas:
            identifier = self._safe_int(item.get("id"))
            election_year = self._safe_int(item.get("anoEleicao"))
            if identifier is None:
                continue
            if election_year is not None and election_year < 1986:
                continue
            legislaturas_validas.append(identifier)

        membros_por_legislatura: dict[int, list[dict]] = {}
        for legislatura in legislaturas_validas:
            try:
                membros_por_legislatura[legislatura] = await sync_collector.fetch_orgaos_deputados_por_legislatura(legislatura)
            except httpx.HTTPError:
                self._record_data_issue(
                    db,
                    issue_type="source_fetch_error",
                    entity_type="politician_legislature_batch",
                    entity_id=str(legislatura),
                    severity="warning",
                    description=f"Falha ao buscar membros de órgãos na legislatura {legislatura}.",
                )
                membros_por_legislatura[legislatura] = []

        memberships_by_deputy: dict[int, list[dict]] = {}
        for legislatura, membros in membros_por_legislatura.items():
            for item in membros:
                deputado_id = self._safe_int(item.get("idDeputado") or item.get("deputado_id") or item.get("id"))
                if deputado_id is None:
                    continue
                memberships_by_deputy.setdefault(deputado_id, []).append({**item, "legislatura": legislatura})

        total_historical_deputies = len(deputados_historicos)
        for index, deputy in enumerate(deputados_historicos, start=1):
            deputado_id = self._safe_int(deputy.get("id"))
            if deputado_id is None:
                continue

            if index == 1 or index % 25 == 0:
                self._update_historical_checkpoint(
                    sync_run,
                    requested_start_year=requested_start_year,
                    effective_start_year=effective_start_year,
                    end_year=end_year,
                    resume=resume,
                    imported_bills=imported_bills,
                    updated_bills=updated_bills,
                    imported_politicians=imported,
                    updated_politicians=updated,
                    source_errors=source_errors,
                    phase="historical_politicians",
                    current_deputy_index=index,
                    total_historical_deputies=total_historical_deputies,
                    current_deputy_id=deputado_id,
                )
                db.commit()

            deputy_summary = {
                "id": deputado_id,
                "nome": deputy.get("nome") or deputy.get("nomeParlamentar") or deputy.get("ultimoNome") or "Nome não informado",
                "siglaPartido": deputy.get("siglaPartido") or deputy.get("ultimoPartido") or "N/A",
                "siglaUf": deputy.get("siglaUf") or deputy.get("ultimoUF") or "BR",
                "urlFoto": deputy.get("urlFoto"),
                "municipio": deputy.get("municipioNascimento"),
            }
            imported_current, updated_current = await self._upsert_politician(db, deputado_id, sync_started_at, deputy_summary=deputy_summary)
            imported += int(imported_current)
            updated += int(updated_current)

            memberships = memberships_by_deputy.get(deputado_id, [])
            for membership in memberships:
                legislatura = self._safe_int(membership.get("legislatura"))
                partido = membership.get("siglaPartido") or deputy_summary.get("siglaPartido") or "N/A"
                uf = membership.get("siglaUf") or deputy_summary.get("siglaUf") or "BR"
                source_key = self._build_source_key("camara-historico", f"{deputado_id}:{legislatura or 'na'}")
                imported_snapshot, updated_snapshot = self._upsert_historical_politician_snapshot(
                    db,
                    canonical_id=deputado_id,
                    nome=deputy_summary["nome"],
                    partido=partido,
                    uf=uf,
                    cidade=deputy.get("municipioNascimento"),
                    legislatura=legislatura,
                    mandato_inicio=membership.get("dataInicio") or membership.get("dataInicioExercicio"),
                    mandato_fim=membership.get("dataFim") or membership.get("dataFimExercicio"),
                    origem_externa_id=source_key,
                    origem_dados={"deputado": deputy, "membro_legislatura": membership},
                    sync_started_at=sync_started_at,
                )
                imported += int(imported_snapshot)
                updated += int(updated_snapshot)

        self._update_historical_checkpoint(
            sync_run,
            requested_start_year=requested_start_year,
            effective_start_year=effective_start_year,
            end_year=end_year,
            resume=resume,
            imported_bills=imported_bills,
            updated_bills=updated_bills,
            imported_politicians=imported,
            updated_politicians=updated,
            source_errors=source_errors,
            phase="historical_politicians_completed",
            current_deputy_index=total_historical_deputies,
            total_historical_deputies=total_historical_deputies,
        )
        db.commit()

        return imported, updated

    async def _upsert_politician(self, db: Session, deputado_id: int, sync_started_at: datetime, deputy_summary: dict | None = None) -> tuple[bool, bool]:
        source_key = self._build_source_key("camara", deputado_id)
        entity = db.query(PoliticianEntity).filter(PoliticianEntity.origem_externa_id == source_key).one_or_none()
        if entity is None:
            entity = db.get(PoliticianEntity, deputado_id)

        if deputy_summary is None:
            try:
                deputy_summary = await sync_collector.fetch_deputado(deputado_id)
            except httpx.HTTPError:
                deputy_summary = {}

        try:
            deputado_detalhe = await sync_collector.fetch_deputado(deputado_id)
        except httpx.HTTPError:
            deputado_detalhe = deputy_summary or {}

        try:
            deputado_historico = await sync_collector.fetch_deputado_historico(deputado_id)
        except httpx.HTTPError:
            deputado_historico = []

        try:
            deputado_eventos = await sync_collector.fetch_deputado_eventos(deputado_id)
        except httpx.HTTPError:
            deputado_eventos = []

        try:
            deputado_mandatos_externos = await sync_collector.fetch_deputado_mandatos_externos(deputado_id)
        except httpx.HTTPError:
            deputado_mandatos_externos = []

        payload_base = deputy_summary or deputado_detalhe or {}
        ativo, status_politico = self._normalize_politician_status(payload_base, deputado_detalhe)
        cidade = (
            deputado_detalhe.get("municipioNascimento")
            or deputado_detalhe.get("cidade")
            or payload_base.get("municipio")
        )

        politician_payload = {
            "canonical_politician_id": None,
            "nome": payload_base.get("nome") or deputado_detalhe.get("nome") or "Nome não informado",
            "partido": payload_base.get("siglaPartido") or deputado_detalhe.get("siglaPartido") or "N/A",
            "uf": payload_base.get("siglaUf") or deputado_detalhe.get("siglaUf") or "BR",
            "cidade": cidade,
            "cargo": "Deputado Federal",
            "casa": "Câmara dos Deputados",
            "foto_url": payload_base.get("urlFoto") or deputado_detalhe.get("urlFoto"),
            "ativo": ativo,
            "status_politico": status_politico,
            "identidade_tipo": "atual",
            "legislatura": self._safe_int((deputado_detalhe.get("ultimoStatus") or {}).get("idLegislatura") or payload_base.get("idLegislatura")),
            "mandato_inicio": (deputado_detalhe.get("ultimoStatus") or {}).get("data"),
            "mandato_fim": None,
            "fonte": "camara",
            "origem_externa_id": source_key,
            "origem_dados": {
                "resumo": deputy_summary,
                "detalhe": deputado_detalhe,
                "historico": deputado_historico,
                "eventos": deputado_eventos,
                "mandatosExternos": deputado_mandatos_externos,
            },
            "ultima_sincronizacao": sync_started_at,
        }

        if entity is None:
            entity = PoliticianEntity(id=deputado_id, **politician_payload)
            db.add(entity)
            return True, False

        for field, value in politician_payload.items():
            setattr(entity, field, value)
        return False, True

    @staticmethod
    def _collect_related_politician_ids(tramitacoes: list[dict], vote_sessions: list[dict]) -> set[int]:
        politician_ids: set[int] = set()
        for item in tramitacoes:
            if not isinstance(item, dict):
                continue
            uri_ultimo_relator = item.get("uriUltimoRelator")
            if isinstance(uri_ultimo_relator, str) and "/" in uri_ultimo_relator:
                maybe_id = uri_ultimo_relator.rstrip("/").split("/")[-1]
                if maybe_id.isdigit():
                    politician_ids.add(int(maybe_id))
        for session in vote_sessions:
            for vote in session.get("votos", []):
                politician_id = vote.get("politician_id")
                if isinstance(politician_id, int):
                    politician_ids.add(politician_id)
        return politician_ids

    async def _upsert_bill_from_summary(
        self,
        db: Session,
        proposicao_resumo: dict,
        fallback_year: int,
        sync_started_at: datetime,
        prefetched_bundle: dict | None = None,
        authors_by_proposition: dict[int, list[dict]] | None = None,
        themes_by_proposition: dict[int, list[dict]] | None = None,
        sync_related_politicians: bool = False,
    ) -> tuple[int, int, int, int]:
        proposicao_id = proposicao_resumo.get("id")
        if proposicao_id is None:
            return 0, 0, 0, 0

        try:
            if prefetched_bundle is not None:
                if prefetched_bundle.get("error") is not None:
                    raise prefetched_bundle["error"]
                detalhe = prefetched_bundle.get("detalhe") or {}
                tramitacoes = prefetched_bundle.get("tramitacoes") or []
                votacoes = prefetched_bundle.get("votacoes") or []
            else:
                detalhe = await sync_collector.fetch_proposicao(proposicao_id)
                tramitacoes = await sync_collector.fetch_tramitacoes(proposicao_id)
                votacoes = await sync_collector.fetch_votacoes(proposicao_id)
        except httpx.HTTPError:
            self._record_data_issue(
                db,
                issue_type="source_fetch_error",
                entity_type="bill",
                entity_id=str(proposicao_id),
                severity="error",
                description=f"Falha ao buscar detalhe, tramitações ou votações da proposição {proposicao_id} na Câmara.",
            )
            return 0, 0, 0, 1

        self._resolve_data_issues(
            db,
            issue_types=["source_fetch_error", "empty_sync_result"],
            entity_type="bill",
            entity_id=str(proposicao_id),
        )

        status_proposicao = detalhe.get("statusProposicao") or {}
        source_key = self._build_source_key("camara-proposicao", proposicao_id)
        entity = db.query(BillEntity).filter(BillEntity.origem_externa_id == source_key).one_or_none()
        vote_sessions = await self._populate_votes_for_sessions(sync_normalizer.extract_voting_sessions(votacoes))
        proposition_authors = (authors_by_proposition or {}).get(proposicao_id, [])
        proposition_themes = (themes_by_proposition or {}).get(proposicao_id, [])
        sigla = detalhe.get("siglaTipo") or proposicao_resumo.get("siglaTipo") or "PL"
        relevance_score = sync_normalizer.calculate_legislative_relevance_score(
            proposicao_resumo,
            detalhe=detalhe,
            status_proposicao=status_proposicao,
            votacoes=votacoes,
            autores=proposition_authors,
        )
        bill_payload = {
            "sigla": sigla,
            "numero": detalhe.get("numero") or proposicao_resumo.get("numero") or 0,
            "ano": detalhe.get("ano") or proposicao_resumo.get("ano") or fallback_year,
            "ementa": detalhe.get("ementa") or proposicao_resumo.get("ementa") or "Ementa não informada.",
            "resumo": detalhe.get("ementa") or proposicao_resumo.get("ementa") or "Resumo não informado.",
            "autor_principal": sync_normalizer.build_authorship_summary(proposition_authors, detalhe, proposicao_resumo),
            "casa_origem": "Câmara dos Deputados",
            "status_atual": status_proposicao.get("descricaoSituacao") or status_proposicao.get("descricaoTramitacao") or "Em tramitação",
            "tema": sync_normalizer.build_theme_summary(proposition_themes),
            "impacto_financeiro": False,
            "precisa_plenario": sync_normalizer.infer_requires_plenary(sigla, status_proposicao, votacoes),
            "aprovada": sync_normalizer.is_bill_approved(status_proposicao),
            "data_apresentacao": detalhe.get("dataApresentacao"),
            "data_ultima_acao": status_proposicao.get("dataHora") or status_proposicao.get("data"),
            "timeline": self._build_timeline(tramitacoes, status_proposicao),
            "votacoes": vote_sessions,
            "fonte": "camara",
            "origem_externa_id": source_key,
            "origem_dados": {
                "resumo": proposicao_resumo,
                "detalhe": detalhe,
                "tramitacoes": tramitacoes,
                "votacoes": votacoes,
                "autores": proposition_authors,
                "temas": proposition_themes,
                "relevancia_historica": sync_normalizer.is_historically_relevant_proposition(proposicao_resumo),
            },
            "ultima_sincronizacao": sync_started_at,
        }

        imported_bills = 0
        updated_bills = 0
        imported_politicians = 0
        updated_politicians = 0

        if entity is None:
            entity = BillEntity(id=proposicao_id, **bill_payload)
            db.add(entity)
            imported_bills += 1
        else:
            for field, value in bill_payload.items():
                setattr(entity, field, value)
            updated_bills += 1

        self._store_vote_events(db, proposicao_id, f"{bill_payload['sigla']} {bill_payload['numero']}/{bill_payload['ano']}", vote_sessions, "camara")

        if sync_related_politicians:
            related_ids = self._collect_related_politician_ids(tramitacoes, vote_sessions)
            for politician_id in related_ids:
                imported, updated = await self._upsert_politician(db, politician_id, sync_started_at)
                imported_politicians += int(imported)
                updated_politicians += int(updated)

        return imported_bills, updated_bills, imported_politicians, updated_politicians

    async def run_historical_backfill(
        self,
        db: Session,
        start_year: int = 1988,
        end_year: int | None = None,
        items_per_year: int = 0,
        resume: bool = False,
        batch_size: int = 25,
        max_concurrency: int = 5,
    ) -> dict[str, int | str | bool]:
        requested_start_year = start_year
        final_year = end_year or datetime.utcnow().year
        resumed_from_checkpoint = False
        if resume:
            checkpoint = self._get_last_historical_checkpoint(db)
            checkpoint_year = checkpoint.get("last_completed_year") if isinstance(checkpoint, dict) else None
            if isinstance(checkpoint_year, int):
                start_year = max(start_year, checkpoint_year + 1)
                resumed_from_checkpoint = start_year != requested_start_year

        imported_bills = 0
        updated_bills = 0
        imported_politicians = 0
        updated_politicians = 0
        errors = 0
        lock_handle = job_lock_service.acquire("sync:historical_backfill", ttl_seconds=60 * 60 * 6)
        if not lock_handle.acquired:
            return {
                "status": "skipped",
                "reason": "historical_backfill_already_running",
                "resume": resume,
                "requested_start_year": requested_start_year,
                "start_year": start_year,
                "end_year": final_year,
            }
        sync_run = self._start_sync_run(
            db,
            source="camara",
            sync_type="historical_backfill",
            metadata={
                "requested_start_year": requested_start_year,
                "effective_start_year": start_year,
                "end_year": final_year,
                "items_per_year": items_per_year,
                "items_per_year_semantics": "0 means unlimited annual coverage",
                "batch_size": batch_size,
                "max_concurrency": max_concurrency,
                "resume": resume,
            },
        )
        sync_collector.set_raw_recorder(lambda path, url, params, payload: self._record_raw_payload(db, path, url, params, payload))

        try:
            sync_started_at = datetime.utcnow()
            self._update_historical_checkpoint(
                sync_run,
                requested_start_year=requested_start_year,
                effective_start_year=start_year,
                end_year=final_year,
                resume=resume,
                imported_bills=imported_bills,
                updated_bills=updated_bills,
                imported_politicians=imported_politicians,
                updated_politicians=updated_politicians,
                source_errors=errors,
                phase="starting_historical_politicians",
            )
            db.commit()

            imported_hist_politicians, updated_hist_politicians = await self._sync_historical_politicians_backfill(
                db,
                sync_started_at,
                sync_run=sync_run,
                requested_start_year=requested_start_year,
                effective_start_year=start_year,
                end_year=final_year,
                resume=resume,
                imported_bills=imported_bills,
                updated_bills=updated_bills,
                source_errors=errors,
            )
            imported_politicians += imported_hist_politicians
            updated_politicians += updated_hist_politicians
            db.commit()

            for year in range(start_year, final_year + 1):
                try:
                    proposicoes = await sync_collector.fetch_proposicoes_por_ano_download(year)
                    autores_anuais = await sync_collector.fetch_proposicoes_autores_por_ano_download(year)
                    temas_anuais = await sync_collector.fetch_proposicoes_temas_por_ano_download(year)
                except httpx.HTTPError:
                    self._record_data_issue(
                        db,
                        issue_type="source_fetch_error",
                        entity_type="bill_batch",
                        entity_id=str(year),
                        severity="error",
                        description=f"Falha ao buscar proposições do ano {year} na Câmara durante o backfill histórico.",
                    )
                    errors += 1
                    continue

                self._resolve_data_issues(
                    db,
                    issue_types=["source_fetch_error"],
                    entity_type="bill_batch",
                    entity_id=str(year),
                )

                proposicoes_ordenadas = sorted(
                    proposicoes,
                    key=lambda item: (
                        sync_normalizer.is_historically_relevant_proposition(item),
                        sync_normalizer.extract_presentation_month(item),
                        self._extract_proposition_id(item) or 0,
                    ),
                    reverse=True,
                )
                if items_per_year > 0:
                    proposicoes_ordenadas = proposicoes_ordenadas[:items_per_year]

                authors_by_proposition: dict[int, list[dict]] = {}
                for autor in autores_anuais:
                    proposition_id = self._safe_int(autor.get("idProposicao") or autor.get("proposicao_id") or autor.get("id"))
                    if proposition_id is None:
                        continue
                    authors_by_proposition.setdefault(proposition_id, []).append(autor)

                themes_by_proposition: dict[int, list[dict]] = {}
                for tema in temas_anuais:
                    proposition_id = self._safe_int(tema.get("idProposicao") or tema.get("proposicao_id") or tema.get("id"))
                    if proposition_id is None:
                        continue
                    themes_by_proposition.setdefault(proposition_id, []).append(tema)

                sync_started_at = datetime.utcnow()
                proposicoes_por_mes: dict[int, list[dict]] = {}
                for proposicao in proposicoes_ordenadas:
                    mes = sync_normalizer.extract_presentation_month(proposicao)
                    proposicoes_por_mes.setdefault(mes, []).append(proposicao)

                for mes in sorted(proposicoes_por_mes.keys(), reverse=True):
                    lotes = self._chunk_list(proposicoes_por_mes[mes], batch_size)
                    for indice_lote, lote in enumerate(lotes, start=1):
                        bundles = await self._fetch_proposition_bundles(lote, max_concurrency=max_concurrency)
                        for bundle in bundles:
                            proposicao_resumo = bundle.get("resumo") or {}
                            imported_bill_count, updated_bill_count, imported_politician_count, updated_politician_count = await self._upsert_bill_from_summary(
                                db,
                                proposicao_resumo,
                                year,
                                sync_started_at,
                                prefetched_bundle=bundle,
                                authors_by_proposition=authors_by_proposition,
                                themes_by_proposition=themes_by_proposition,
                                sync_related_politicians=True,
                            )
                            imported_bills += imported_bill_count
                            updated_bills += updated_bill_count
                            imported_politicians += imported_politician_count
                            updated_politicians += updated_politician_count
                            if imported_bill_count == updated_bill_count == imported_politician_count == updated_politician_count == 0:
                                proposicao_id = proposicao_resumo.get("id")
                                self._record_data_issue(
                                    db,
                                    issue_type="empty_sync_result",
                                    entity_type="bill",
                                    entity_id=str(proposicao_id) if proposicao_id is not None else None,
                                    severity="warning",
                                    description="A sincronização da proposição não importou nem atualizou registros relacionados.",
                                )
                                errors += 1

                        sync_run.checkpoint_json = {
                            "requested_start_year": requested_start_year,
                            "effective_start_year": start_year,
                            "last_completed_year": year,
                            "last_completed_month": mes if mes > 0 else None,
                            "last_completed_batch": indice_lote,
                            "end_year": final_year,
                            "resume": resume,
                            "available_bills_in_year": len(proposicoes),
                            "processed_bills_in_year": len(proposicoes_ordenadas),
                            "relevant_bills_in_year": sum(1 for item in proposicoes if sync_normalizer.is_historically_relevant_proposition(item)),
                            "authors_loaded_in_year": len(autores_anuais),
                            "themes_loaded_in_year": len(temas_anuais),
                            "batch_size": batch_size,
                            "max_concurrency": max_concurrency,
                            "imported_bills": imported_bills,
                            "updated_bills": updated_bills,
                            "imported_politicians": imported_politicians,
                            "updated_politicians": updated_politicians,
                            "source_errors": errors,
                        }
                        db.commit()
        except Exception as exc:
            self._finish_sync_run(
                sync_run,
                status="failed",
                processed_count=imported_bills + updated_bills + imported_politicians + updated_politicians,
                error_count=errors + 1,
                checkpoint=sync_run.checkpoint_json if isinstance(sync_run.checkpoint_json, dict) else None,
                metadata={
                    "requested_start_year": requested_start_year,
                    "effective_start_year": start_year,
                    "end_year": final_year,
                    "resume": resume,
                    "batch_size": batch_size,
                    "max_concurrency": max_concurrency,
                    "imported_bills": imported_bills,
                    "updated_bills": updated_bills,
                    "imported_politicians": imported_politicians,
                    "updated_politicians": updated_politicians,
                    "source_errors": errors,
                    "exception": repr(exc),
                },
            )
            db.commit()
            raise
        finally:
            sync_collector.clear_raw_recorder()
            job_lock_service.release(lock_handle)

        self.last_run_at = datetime.utcnow()
        final_checkpoint = sync_run.checkpoint_json if isinstance(sync_run.checkpoint_json, dict) else {}
        result = {
            "status": "ok",
            "resume": resume,
            "resumed_from_checkpoint": resumed_from_checkpoint,
            "requested_start_year": requested_start_year,
            "start_year": start_year,
            "end_year": final_year,
            "items_per_year": items_per_year,
            "batch_size": batch_size,
            "max_concurrency": max_concurrency,
            "imported_bills": imported_bills,
            "updated_bills": updated_bills,
            "imported_politicians": imported_politicians,
            "updated_politicians": updated_politicians,
            "source_errors": errors,
            "last_run_at": self.last_run_at.isoformat() + "Z",
        }
        self._finish_sync_run(
            sync_run,
            status="completed",
            processed_count=imported_bills + updated_bills + imported_politicians + updated_politicians,
            error_count=errors,
            checkpoint={
                "requested_start_year": requested_start_year,
                "effective_start_year": start_year,
                "last_completed_year": final_year if start_year <= final_year else None,
                "last_completed_month": final_checkpoint.get("last_completed_month"),
                "last_completed_batch": final_checkpoint.get("last_completed_batch"),
                "end_year": final_year,
                "resume": resume,
                "available_bills_in_year": final_checkpoint.get("available_bills_in_year"),
                "processed_bills_in_year": final_checkpoint.get("processed_bills_in_year"),
                "relevant_bills_in_year": final_checkpoint.get("relevant_bills_in_year"),
                "authors_loaded_in_year": final_checkpoint.get("authors_loaded_in_year"),
                "themes_loaded_in_year": final_checkpoint.get("themes_loaded_in_year"),
                "batch_size": batch_size,
                "max_concurrency": max_concurrency,
                "imported_bills": imported_bills,
                "updated_bills": updated_bills,
                "imported_politicians": imported_politicians,
                "updated_politicians": updated_politicians,
                "source_errors": errors,
            },
            metadata=result,
        )
        db.commit()
        return result

    async def run_daily_sync(self, db: Session) -> dict[str, str | int]:
        lock_handle = job_lock_service.acquire("sync:daily", ttl_seconds=60 * 60)
        if not lock_handle.acquired:
            return {
                "status": "skipped",
                "message": "Já existe uma sincronização diária em andamento.",
            }
        sync_run = self._start_sync_run(db, source="camara", sync_type="daily_sync")
        sync_collector.set_raw_recorder(lambda path, url, params, payload: self._record_raw_payload(db, path, url, params, payload))
        try:
            deputados = await sync_collector.fetch_deputados(all_pages=True)
            bill_errors = 0
            try:
                proposicoes = await sync_collector.fetch_proposicoes(all_pages=True)
            except httpx.HTTPError:
                proposicoes = []
                self._record_data_issue(
                    db,
                    issue_type="source_fetch_error",
                    entity_type="bill_batch",
                    severity="error",
                    description="Falha ao buscar lote diário de proposições da Câmara.",
                )
                bill_errors = 1
            else:
                self._resolve_data_issues(
                    db,
                    issue_types=["source_fetch_error"],
                    entity_type="bill_batch",
                    entity_id=None,
                )

            imported = 0
            updated = 0
            imported_bills = 0
            updated_bills = 0
            sync_started_at = datetime.utcnow()
            for deputado in deputados:
                deputado_id = deputado.get("id")
                if deputado_id is None:
                    continue
                politician_imported, politician_updated = await self._upsert_politician(db, deputado_id, sync_started_at, deputy_summary=deputado)
                imported += int(politician_imported)
                updated += int(politician_updated)

            for proposicao_resumo in proposicoes:
                imported_bill_count, updated_bill_count, _, _ = await self._upsert_bill_from_summary(
                    db,
                    proposicao_resumo,
                    sync_started_at.year,
                    sync_started_at,
                    sync_related_politicians=False,
                )
                imported_bills += imported_bill_count
                updated_bills += updated_bill_count
                if imported_bill_count == updated_bill_count == 0:
                    proposicao_id = proposicao_resumo.get("id")
                    self._record_data_issue(
                        db,
                        issue_type="empty_sync_result",
                        entity_type="bill",
                        entity_id=str(proposicao_id) if proposicao_id is not None else None,
                        severity="warning",
                        description="A sincronização diária da proposição não importou nem atualizou registros.",
                    )
                    bill_errors += 1
        finally:
            sync_collector.clear_raw_recorder()
            job_lock_service.release(lock_handle)

        db.commit()
        self.last_run_at = datetime.utcnow()
        result = {
            "status": "ok",
            "message": "Sincronização inicial da Câmara concluída. Senado e tramitações detalhadas serão integrados na próxima etapa.",
            "imported_politicians": imported,
            "updated_politicians": updated,
            "imported_bills": imported_bills,
            "updated_bills": updated_bills,
            "bill_source_errors": bill_errors,
            "last_run_at": self.last_run_at.isoformat() + "Z",
        }
        self._finish_sync_run(
            sync_run,
            status="completed",
            processed_count=imported + updated + imported_bills + updated_bills,
            error_count=bill_errors,
            metadata=result,
        )
        db.commit()
        return result


sync_service = SyncService()
