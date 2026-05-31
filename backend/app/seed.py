from sqlalchemy import inspect, text

from app.data import HIGHLIGHTS
from app.db import Base, SessionLocal, engine
from app.entities import BillEntity, DataIssueEntity, HighlightEntity, PoliticianEntity, RawSourceRecordEntity, SyncRunEntity, VoteEventEntity


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_development_schema()
    seed_db()


def ensure_development_schema() -> None:
    inspector = inspect(engine)
    dialect = engine.dialect.name

    politician_columns = {column['name'] for column in inspector.get_columns('politicians')} if inspector.has_table('politicians') else set()
    bill_columns = {column['name'] for column in inspector.get_columns('bills')} if inspector.has_table('bills') else set()
    vote_event_columns = {column['name'] for column in inspector.get_columns('vote_events')} if inspector.has_table('vote_events') else set()

    json_type = 'JSON' if dialect == 'postgresql' else 'TEXT'
    timestamp_type = 'TIMESTAMP'

    statements: list[str] = []
    if 'fonte' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN fonte VARCHAR(50) DEFAULT 'seed'")
    if 'cidade' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN cidade VARCHAR(120)")
    if 'origem_externa_id' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN origem_externa_id VARCHAR(100)")
    if 'origem_dados' not in politician_columns:
        statements.append(f"ALTER TABLE politicians ADD COLUMN origem_dados {json_type}")
    if 'ultima_sincronizacao' not in politician_columns:
        statements.append(f"ALTER TABLE politicians ADD COLUMN ultima_sincronizacao {timestamp_type}")
    if 'status_politico' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN status_politico VARCHAR(50) DEFAULT 'ativo'")
    if 'canonical_politician_id' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN canonical_politician_id INTEGER")
    if 'identidade_tipo' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN identidade_tipo VARCHAR(30) DEFAULT 'atual'")
    if 'legislatura' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN legislatura INTEGER")
    if 'mandato_inicio' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN mandato_inicio VARCHAR(50)")
    if 'mandato_fim' not in politician_columns:
        statements.append("ALTER TABLE politicians ADD COLUMN mandato_fim VARCHAR(50)")

    if 'fonte' not in bill_columns:
        statements.append("ALTER TABLE bills ADD COLUMN fonte VARCHAR(50) DEFAULT 'seed'")
    if 'origem_externa_id' not in bill_columns:
        statements.append("ALTER TABLE bills ADD COLUMN origem_externa_id VARCHAR(100)")
    if 'origem_dados' not in bill_columns:
        statements.append(f"ALTER TABLE bills ADD COLUMN origem_dados {json_type}")
    if 'ultima_sincronizacao' not in bill_columns:
        statements.append(f"ALTER TABLE bills ADD COLUMN ultima_sincronizacao {timestamp_type}")
    if 'aprovada' not in bill_columns:
        statements.append("ALTER TABLE bills ADD COLUMN aprovada BOOLEAN DEFAULT FALSE")
    if 'data_apresentacao' not in bill_columns:
        statements.append("ALTER TABLE bills ADD COLUMN data_apresentacao VARCHAR(50)")
    if 'data_ultima_acao' not in bill_columns:
        statements.append("ALTER TABLE bills ADD COLUMN data_ultima_acao VARCHAR(50)")

    if not inspector.has_table('vote_events'):
        statements.append(
            "CREATE TABLE vote_events (id INTEGER PRIMARY KEY AUTOINCREMENT, politician_id INTEGER NULL, politician_name VARCHAR(255) NOT NULL, bill_id INTEGER NULL, bill_label VARCHAR(100) NOT NULL, votacao_id VARCHAR(50) NULL, data VARCHAR(50) NULL, orgao VARCHAR(255) NOT NULL, resultado VARCHAR(255) NULL, voto VARCHAR(50) NOT NULL, partido VARCHAR(50) NULL, uf VARCHAR(10) NULL, fonte VARCHAR(50) NOT NULL DEFAULT 'seed')"
        )
    elif 'votacao_id' not in vote_event_columns:
        statements.append("ALTER TABLE vote_events ADD COLUMN votacao_id VARCHAR(50)")

    if not inspector.has_table(RawSourceRecordEntity.__tablename__):
        Base.metadata.tables[RawSourceRecordEntity.__tablename__].create(bind=engine, checkfirst=True)

    if not inspector.has_table(SyncRunEntity.__tablename__):
        Base.metadata.tables[SyncRunEntity.__tablename__].create(bind=engine, checkfirst=True)

    if not inspector.has_table(DataIssueEntity.__tablename__):
        Base.metadata.tables[DataIssueEntity.__tablename__].create(bind=engine, checkfirst=True)

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def seed_db() -> None:
    with SessionLocal() as session:
        has_highlights = session.query(HighlightEntity).first() is not None

        if not has_highlights:
            session.add_all(
                [
                    HighlightEntity(
                        title=item.title,
                        subtitle=item.subtitle,
                        metric=item.metric,
                    )
                    for item in HIGHLIGHTS
                ]
            )

        session.commit()
