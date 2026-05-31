from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.entities import SyncRunEntity
from app.models import DataIssueSummary, HistoricalCheckpointSummary, HistoricalCoverageSummary, SyncRunSummary, SyncStatusSummary
from app.services.sync import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatusSummary)
def get_sync_status(db: Session = Depends(get_db)):
    return sync_service.get_sync_status(db)


@router.get("/runs", response_model=list[SyncRunSummary])
def list_sync_runs(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(SyncRunEntity)
        .order_by(SyncRunEntity.started_at.desc(), SyncRunEntity.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [
        SyncRunSummary(
            id=row.id,
            source=row.source,
            sync_type=row.sync_type,
            status=row.status,
            started_at=row.started_at.isoformat() + "Z" if row.started_at else None,
            finished_at=row.finished_at.isoformat() + "Z" if row.finished_at else None,
            processed_count=row.processed_count,
            error_count=row.error_count,
            checkpoint_json=row.checkpoint_json,
            metadata_json=row.metadata_json,
        )
        for row in rows
    ]


@router.get("/issues", response_model=list[DataIssueSummary])
def list_sync_issues(
    status: str | None = None,
    severity: str | None = None,
    issue_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return sync_service.list_data_issues(
        db,
        status=status,
        severity=severity,
        issue_type=issue_type,
        limit=limit,
    )


@router.get("/historical/checkpoint", response_model=HistoricalCheckpointSummary)
def get_historical_checkpoint(db: Session = Depends(get_db)):
    return sync_service.get_last_historical_checkpoint(db)


@router.get("/historical/coverage", response_model=HistoricalCoverageSummary)
async def get_historical_coverage(db: Session = Depends(get_db)):
    return await sync_service.get_historical_coverage(db)


@router.post("/daily")
async def run_daily_sync(db: Session = Depends(get_db)):
    return await sync_service.run_daily_sync(db)


@router.post("/historical")
async def run_historical_sync(
    start_year: int = 1988,
    end_year: int | None = None,
    items_per_year: int = 0,
    resume: bool = False,
    batch_size: int = 25,
    max_concurrency: int = 5,
    db: Session = Depends(get_db),
):
    return await sync_service.run_historical_backfill(
        db,
        start_year=start_year,
        end_year=end_year,
        items_per_year=items_per_year,
        resume=resume,
        batch_size=batch_size,
        max_concurrency=max_concurrency,
    )
