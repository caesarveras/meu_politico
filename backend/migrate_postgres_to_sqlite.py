from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.entities import (
    BillEntity,
    DataIssueEntity,
    HighlightEntity,
    PoliticianEntity,
    RawSourceRecordEntity,
    SyncRunEntity,
    VoteEventEntity,
)

TABLES = [
    HighlightEntity,
    PoliticianEntity,
    BillEntity,
    VoteEventEntity,
    RawSourceRecordEntity,
    SyncRunEntity,
    DataIssueEntity,
]


def _normalize_sqlite_url(value: str) -> str:
    if value.startswith("sqlite:///"):
        return value
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return f"sqlite:///{path}"


def _as_payload(row: object) -> dict:
    return {
        column.name: getattr(row, column.name)
        for column in row.__table__.columns
    }


def migrate(source_url: str, sqlite_url: str, *, reset_destination: bool) -> dict[str, int]:
    source_engine = create_engine(source_url, future=True, pool_pre_ping=True)
    destination_engine = create_engine(sqlite_url, future=True, pool_pre_ping=True)

    Base.metadata.create_all(bind=destination_engine)

    counts: dict[str, int] = {}
    with Session(source_engine) as source_session, Session(destination_engine) as destination_session:
        for entity in reversed(TABLES):
            if reset_destination:
                destination_session.query(entity).delete()
        destination_session.commit()

        for entity in TABLES:
            rows = source_session.execute(select(entity)).scalars().all()
            payloads = [_as_payload(row) for row in rows]
            if payloads:
                destination_session.execute(entity.__table__.insert(), payloads)
            counts[entity.__tablename__] = len(payloads)
        destination_session.commit()

    source_engine.dispose()
    destination_engine.dispose()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--sqlite-path", default="meuspoliticos.db")
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    sqlite_url = _normalize_sqlite_url(args.sqlite_path)
    counts = migrate(args.source_url, sqlite_url, reset_destination=not args.no_reset)
    for table_name, count in counts.items():
        print(f"{table_name}\t{count}")


if __name__ == "__main__":
    main()
