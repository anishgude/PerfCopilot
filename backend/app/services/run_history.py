from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.service import analyze_payload
from app.db.models import AnalysisRun
from app.schemas.benchmark import (
    AnalyzeResponse,
    BenchmarkPayload,
    RunDetailResponse,
    RunListItem,
    UploadAnalyzeResponse,
)


def _title_from_payload(payload: BenchmarkPayload, fallback: str | None = None) -> str:
    if fallback:
        return fallback
    if payload.task.strip():
        return payload.task.strip()[:120]
    return f"{payload.language} benchmark run"


def _to_list_item(row: AnalysisRun) -> RunListItem:
    return RunListItem(
        id=row.id,
        created_at=row.created_at,
        title=row.title,
        language=row.language,
        status=row.status,
        slowdown_at_max_pct=row.slowdown_at_max_pct,
        a_best_fit=row.a_best_fit,
        b_best_fit=row.b_best_fit,
    )


def _to_detail(row: AnalysisRun) -> RunDetailResponse:
    return RunDetailResponse(
        id=row.id,
        created_at=row.created_at,
        title=row.title,
        language=row.language,
        task=row.task,
        code=row.code,
        benchmark_json=json.loads(row.benchmark_json),
        raw_model_text=row.raw_model_text,
        parsed_output_json=(
            json.loads(row.parsed_output_json) if row.parsed_output_json else None
        ),
        slowdown_at_max_pct=row.slowdown_at_max_pct,
        slowdown_at_mid_pct=row.slowdown_at_mid_pct,
        memory_growth_pct=row.memory_growth_pct,
        a_best_fit=row.a_best_fit,
        b_best_fit=row.b_best_fit,
        status=row.status,
        error_message=row.error_message,
    )


async def create_run_with_analysis(
    db: Session,
    payload: BenchmarkPayload,
    title: str | None = None,
) -> UploadAnalyzeResponse:
    run = AnalysisRun(
        title=_title_from_payload(payload, title),
        language=payload.language,
        task=payload.task,
        code=payload.code,
        benchmark_json=payload.model_dump_json(),
        status="success",
        a_best_fit=payload.fit.a_best_fit,
        b_best_fit=payload.fit.b_best_fit,
    )

    try:
        result: AnalyzeResponse = await analyze_payload(payload)
        run.raw_model_text = result.raw_model_text
        run.parsed_output_json = (
            result.parsed.model_dump_json() if result.parsed else None
        )
        run.slowdown_at_max_pct = result.computed.slowdown_at_max_pct
        run.slowdown_at_mid_pct = result.computed.slowdown_at_mid_pct
        run.memory_growth_pct = result.computed.memory_growth_at_max_pct
    except Exception as exc:
        run.status = "error"
        run.error_message = str(exc)
        db.add(run)
        db.commit()
        db.refresh(run)
        return UploadAnalyzeResponse(
            run_id=run.id,
            status=run.status,
            computed=None,
            parsed=None,
            raw_model_text=None,
            error_message=run.error_message,
        )

    db.add(run)
    db.commit()
    db.refresh(run)
    return UploadAnalyzeResponse(
        run_id=run.id,
        status=run.status,
        computed=result.computed,
        parsed=result.parsed,
        raw_model_text=result.raw_model_text,
        error_message=None,
    )


def list_runs(db: Session) -> list[RunListItem]:
    rows = db.execute(
        select(AnalysisRun).order_by(AnalysisRun.created_at.desc())
    ).scalars()
    return [_to_list_item(row) for row in rows]


def get_run(db: Session, run_id: int) -> RunDetailResponse | None:
    row = db.get(AnalysisRun, run_id)
    if row is None:
        return None
    return _to_detail(row)


def delete_run(db: Session, run_id: int) -> bool:
    row = db.get(AnalysisRun, run_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
