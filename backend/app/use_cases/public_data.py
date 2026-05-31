from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.legislative_repository import legislative_repository


class PublicDataUseCase:
    def get_supported_languages(self) -> dict[str, list[str]]:
        return {"languages": settings.supported_locales}

    def get_highlights(self, db: Session):
        return legislative_repository.list_highlights(db)

    def list_politicians(
        self,
        db: Session,
        query: str | None = None,
        cargo: list[str] | None = None,
        partido: list[str] | None = None,
        uf: list[str] | None = None,
        cidade: list[str] | None = None,
        status_politico: list[str] | None = None,
        identidade_tipo: str | None = None,
    ):
        return legislative_repository.list_politicians(
            db,
            query=query,
            cargo=cargo,
            partido=partido,
            uf=uf,
            cidade=cidade,
            status_politico=status_politico,
            identidade_tipo=identidade_tipo,
        )

    def get_politician(self, db: Session, politician_id: int):
        politician = legislative_repository.get_politician(db, politician_id)
        if politician is None:
            raise HTTPException(status_code=404, detail="Parlamentar não encontrado")
        return politician

    def list_bills(self, db: Session, sort_by: str | None = None):
        return legislative_repository.list_bills(db, sort_by=sort_by)

    def list_approved_bills(self, db: Session, query: str | None = None, year_from: int | None = None, year_to: int | None = None, sort_by: str | None = None):
        return legislative_repository.list_approved_bills(db, query=query, year_from=year_from, year_to=year_to, sort_by=sort_by)

    def search_approved_bills(
        self,
        db: Session,
        theme: str | None = None,
        author: str | None = None,
        party: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        page: int = 1,
        page_size: int = 12,
        sort_by: str | None = None,
    ):
        return legislative_repository.search_approved_bills(
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

    def get_approved_bill_facets(self, db: Session):
        return legislative_repository.get_approved_bill_facets(db)

    def get_bill(self, db: Session, bill_id: int):
        bill = legislative_repository.get_bill(db, bill_id)
        if bill is None:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return bill

    def get_politician_history(self, db: Session, politician_id: int):
        history = legislative_repository.get_politician_history(db, politician_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Histórico do parlamentar não encontrado")
        return history


public_data_use_case = PublicDataUseCase()
