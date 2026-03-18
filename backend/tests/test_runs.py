import json

from fastapi.testclient import TestClient

from app.db.models import AnalysisRun
from app.db.session import SessionLocal, init_db
from app.main import app
from app.schemas.benchmark import (
    AnalyzeResponse,
    ComputedMetrics,
    FitSummary,
    ParsedDiagnosis,
)
from app.services import run_history as runs

client = TestClient(app)


def _clean_runs() -> None:
    init_db()
    db = SessionLocal()
    try:
        db.query(AnalysisRun).delete()
        db.commit()
    finally:
        db.close()


def _payload() -> dict:
    return {
        "language": "Python",
        "task": "Uploaded benchmark test task",
        "code": "def f(xs): return sum(xs)",
        "n": [1000, 2000, 4000],
        "runtime_a": [3.1, 6.2, 12.4],
        "runtime_b": [4.0, 8.3, 17.6],
        "memory_a": [5.0, 5.1, 5.3],
        "memory_b": [5.5, 6.0, 6.8],
        "fit": {
            "a_best_fit": "O(n)",
            "a_confidence": 0.91,
            "b_best_fit": "O(n)",
            "b_confidence": 0.88,
        },
    }


def _stub_analyze() -> AnalyzeResponse:
    return AnalyzeResponse(
        raw_model_text="Summary:\nStub model\nBest-fit complexity:\nA: O(n), B: O(n)",
        parsed=ParsedDiagnosis(
            summary="Stub model",
            best_fit_complexity="A: O(n), B: O(n)",
            regression_bullets=["42% slowdown"],
            likely_causes=["Extra allocations"],
            evidence=["Runtime B is higher"],
            optimization_direction=["Reduce allocations"],
            risks=["Noise"],
        ),
        computed=ComputedMetrics(
            slowdown_at_mid_pct=33.87,
            slowdown_at_max_pct=41.94,
            memory_growth_at_max_pct=28.3,
            max_n=4000,
            mid_n=2000,
        ),
        fit=FitSummary(
            a_best_fit="O(n)",
            a_confidence=0.91,
            b_best_fit="O(n)",
            b_confidence=0.88,
        ),
    )


def test_upload_benchmark_success(monkeypatch) -> None:
    _clean_runs()

    async def fake_analyze_payload(*_args, **_kwargs) -> AnalyzeResponse:
        return _stub_analyze()

    monkeypatch.setattr(runs, "analyze_payload", fake_analyze_payload)

    response = client.post("/upload-benchmark", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["run_id"] > 0
    assert body["computed"]["slowdown_at_max_pct"] == 41.94


def test_list_get_delete_run(monkeypatch) -> None:
    _clean_runs()

    async def fake_analyze_payload(*_args, **_kwargs) -> AnalyzeResponse:
        return _stub_analyze()

    monkeypatch.setattr(runs, "analyze_payload", fake_analyze_payload)

    upload_response = client.post("/upload-benchmark", json=_payload())
    run_id = upload_response.json()["run_id"]

    list_response = client.get("/runs")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) >= 1
    assert items[0]["id"] == run_id
    assert items[0]["slowdown_at_max_pct"] == 41.94

    get_response = client.get(f"/runs/{run_id}")
    assert get_response.status_code == 200
    run_detail = get_response.json()
    assert run_detail["id"] == run_id
    assert run_detail["benchmark_json"]["task"] == "Uploaded benchmark test task"
    assert run_detail["slowdown_at_mid_pct"] == 33.87
    parsed_json = run_detail["parsed_output_json"]
    if isinstance(parsed_json, str):
        parsed_json = json.loads(parsed_json)
    assert parsed_json["summary"] == "Stub model"

    delete_response = client.delete(f"/runs/{run_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = client.get(f"/runs/{run_id}")
    assert missing_response.status_code == 404
