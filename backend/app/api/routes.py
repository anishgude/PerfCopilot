from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.analysis.service import analyze_payload
from app.core.dependencies import verify_api_key
from app.db.session import get_db
from app.schemas.benchmark import (
    AnalyzeResponse,
    BenchmarkPayload,
    HealthResponse,
    RunDetailResponse,
    RunListItem,
    UploadAnalyzeResponse,
)
from app.services.run_history import (
    create_run_with_analysis,
    delete_run,
    get_run,
    list_runs,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(verify_api_key)],
)
async def analyze(payload: BenchmarkPayload) -> AnalyzeResponse:
    return await analyze_payload(payload)


@router.post(
    "/upload-benchmark",
    response_model=UploadAnalyzeResponse,
    dependencies=[Depends(verify_api_key)],
)
async def upload_benchmark(
    request: Request,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> UploadAnalyzeResponse:
    content_type = request.headers.get("content-type", "")
    payload: BenchmarkPayload
    title: str | None = None

    if "multipart/form-data" in content_type:
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing benchmark file in multipart request",
            )
        if not file.filename or not file.filename.lower().endswith(".json"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be a .json benchmark payload",
            )
        title = os.path.splitext(file.filename)[0]
        try:
            raw_bytes = await file.read()
            payload_dict = json.loads(raw_bytes.decode("utf-8"))
            payload = BenchmarkPayload.model_validate(payload_dict)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid benchmark JSON: {exc}",
            ) from exc
    else:
        try:
            body = await request.json()
            payload = BenchmarkPayload.model_validate(body)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid benchmark JSON body: {exc}",
            ) from exc

    return await create_run_with_analysis(db=db, payload=payload, title=title)


@router.get(
    "/runs",
    response_model=list[RunListItem],
    dependencies=[Depends(verify_api_key)],
)
async def get_runs(db: Session = Depends(get_db)) -> list[RunListItem]:
    return list_runs(db)


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_run_by_id(
    run_id: int,
    db: Session = Depends(get_db),
) -> RunDetailResponse:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run


@router.delete(
    "/runs/{run_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_run_by_id(
    run_id: int,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    deleted = delete_run(db, run_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return {"deleted": True}
