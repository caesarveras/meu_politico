from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bill, Politician
from app.public_models import (
    PublicBillDetail,
    PublicBillStage,
    PublicBillSummary,
    PublicPoliticianDetail,
    PublicPoliticianSummary,
    PublicResponseEnvelope,
    PublicTraceMetadata,
    PublicVoteRecord,
    PublicVoteSession,
)
from app.use_cases.public_data import public_data_use_case

router = APIRouter(prefix="/public", tags=["public"])


def _build_trace(source: str, source_reference: str | None, last_synced_at: str | None) -> PublicTraceMetadata:
    return PublicTraceMetadata(
        source=source,
        source_reference=source_reference,
        last_synced_at=last_synced_at,
        confidence="high" if source != "seed" else "low",
        data_warnings=[] if source != "seed" else ["Registro de seed ou cobertura parcial."],
    )


def _to_public_politician_summary(item: Politician) -> PublicPoliticianSummary:
    return PublicPoliticianSummary(
        id=item.id,
        nome=item.nome,
        partido=item.partido,
        uf=item.uf,
        cidade=item.cidade,
        cargo=item.cargo,
        casa=item.casa,
        foto_url=item.foto_url,
        ativo=item.ativo,
        status_politico=item.status_politico,
        trace=_build_trace(item.fonte, item.origem_externa_id, item.ultima_sincronizacao),
    )


def _to_public_politician_detail(item: Politician) -> PublicPoliticianDetail:
    return PublicPoliticianDetail(
        **_to_public_politician_summary(item).model_dump(),
        origem_externa_id=item.origem_externa_id,
        origem_dados=item.origem_dados,
    )


def _to_public_vote_session(vote_session) -> PublicVoteSession:
    return PublicVoteSession(
        id=vote_session.id,
        titulo=vote_session.titulo,
        orgao=vote_session.orgao,
        data=vote_session.data,
        resultado=vote_session.resultado,
        quorum=vote_session.quorum,
        votos=[
            PublicVoteRecord(
                politician_id=vote.politician_id,
                politician_name=vote.politician_name,
                voto=vote.voto,
                partido=vote.partido,
                uf=vote.uf,
                cidade=vote.cidade,
            )
            for vote in vote_session.votos
        ],
    )


def _to_public_bill_summary(item: Bill) -> PublicBillSummary:
    return PublicBillSummary(
        id=item.id,
        sigla=item.sigla,
        numero=item.numero,
        ano=item.ano,
        ementa=item.ementa,
        resumo=item.resumo,
        autor_principal=item.autor_principal,
        casa_origem=item.casa_origem,
        status_atual=item.status_atual,
        tema=item.tema,
        aprovada=item.aprovada,
        data_apresentacao=item.data_apresentacao,
        data_ultima_acao=item.data_ultima_acao,
        trace=_build_trace(item.fonte, item.origem_externa_id, item.ultima_sincronizacao),
    )


def _to_public_bill_detail(item: Bill) -> PublicBillDetail:
    return PublicBillDetail(
        **_to_public_bill_summary(item).model_dump(),
        impacto_financeiro=item.impacto_financeiro,
        precisa_plenario=item.precisa_plenario,
        timeline=[
            PublicBillStage(
                ordem=stage.ordem,
                fase=stage.fase,
                orgao=stage.orgao,
                descricao=stage.descricao,
                data=stage.data,
                relator_id=stage.relator_id,
                relator_name=stage.relator_name,
                status=stage.status,
            )
            for stage in item.timeline
        ],
        votacoes=[_to_public_vote_session(vote_session) for vote_session in item.votacoes],
    )


@router.get("/config/languages")
def get_supported_languages() -> dict[str, list[str]]:
    return public_data_use_case.get_supported_languages()


@router.get("/highlights")
def get_highlights(db: Session = Depends(get_db)):
    return public_data_use_case.get_highlights(db)


@router.get("/politicians")
def list_politicians(
    query: str | None = None,
    cargo: list[str] | None = Query(default=None),
    partido: list[str] | None = Query(default=None),
    uf: list[str] | None = Query(default=None),
    cidade: list[str] | None = Query(default=None),
    status_politico: list[str] | None = Query(default=None),
    identidade_tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return public_data_use_case.list_politicians(
        db,
        query=query,
        cargo=cargo,
        partido=partido,
        uf=uf,
        cidade=cidade,
        status_politico=status_politico,
        identidade_tipo=identidade_tipo,
    )


@router.get("/politicians/{politician_id}")
def get_politician(politician_id: int, db: Session = Depends(get_db)):
    return public_data_use_case.get_politician(db, politician_id)


@router.get("/stable/politicians", response_model=PublicResponseEnvelope)
def list_politicians_stable(
    query: str | None = None,
    cargo: list[str] | None = Query(default=None),
    partido: list[str] | None = Query(default=None),
    uf: list[str] | None = Query(default=None),
    cidade: list[str] | None = Query(default=None),
    status_politico: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items = public_data_use_case.list_politicians(
        db,
        query=query,
        cargo=cargo,
        partido=partido,
        uf=uf,
        cidade=cidade,
        status_politico=status_politico,
    )
    payload = [_to_public_politician_summary(item) for item in items]
    return PublicResponseEnvelope(data=payload, meta={"count": len(payload), "schema": "public-politicians-stable-v1"})


@router.get("/stable/politicians/{politician_id}", response_model=PublicResponseEnvelope)
def get_politician_stable(politician_id: int, db: Session = Depends(get_db)):
    item = public_data_use_case.get_politician(db, politician_id)
    return PublicResponseEnvelope(data=_to_public_politician_detail(item), meta={"schema": "public-politician-detail-stable-v1"})


@router.get("/bills")
def list_bills(
    sort_by: str | None = Query(default=None, pattern="^(relevance)?$"),
    db: Session = Depends(get_db),
):
    return public_data_use_case.list_bills(db, sort_by=sort_by)


@router.get("/bills/approved")
def list_approved_bills(
    query: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    sort_by: str | None = Query(default=None, pattern="^(relevance|newest|oldest)?$"),
    db: Session = Depends(get_db),
):
    return public_data_use_case.list_approved_bills(db, query=query, year_from=year_from, year_to=year_to, sort_by=sort_by)


@router.get("/bills/approved/facets")
def get_approved_bill_facets(db: Session = Depends(get_db)):
    return public_data_use_case.get_approved_bill_facets(db)


@router.get("/bills/approved/search", response_model=PublicResponseEnvelope)
def search_approved_bills(
    theme: str | None = None,
    author: str | None = None,
    party: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    sort_by: str | None = Query(default=None, pattern="^(relevance|newest|oldest)?$"),
    db: Session = Depends(get_db),
):
    items, total_count = public_data_use_case.search_approved_bills(
        db,
        theme=theme,
        author=author,
        party=party,
        year_from=year_from,
        year_to=year_to,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    return PublicResponseEnvelope(
        data=items,
        meta={
            "count": len(items),
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "schema": "public-approved-bills-search-v1",
        },
    )


@router.get("/bills/{bill_id}")
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    return public_data_use_case.get_bill(db, bill_id)


@router.get("/stable/bills", response_model=PublicResponseEnvelope)
def list_bills_stable(
    sort_by: str | None = Query(default=None, pattern="^(relevance)?$"),
    db: Session = Depends(get_db),
):
    items = public_data_use_case.list_bills(db, sort_by=sort_by)
    payload = [_to_public_bill_summary(item) for item in items]
    return PublicResponseEnvelope(data=payload, meta={"count": len(payload), "schema": "public-bills-stable-v1"})


@router.get("/stable/bills/{bill_id}", response_model=PublicResponseEnvelope)
def get_bill_stable(bill_id: int, db: Session = Depends(get_db)):
    item = public_data_use_case.get_bill(db, bill_id)
    return PublicResponseEnvelope(data=_to_public_bill_detail(item), meta={"schema": "public-bill-detail-stable-v1"})


@router.get("/politicians/{politician_id}/history")
def get_politician_history(politician_id: int, db: Session = Depends(get_db)):
    return public_data_use_case.get_politician_history(db, politician_id)
