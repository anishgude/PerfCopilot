import os

from fastapi.testclient import TestClient

from app.analysis import service as analyzer
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_result() -> None:
    async def fake_call_openai(*_args, **_kwargs) -> str:
        return "\n".join(
            [
                "Summary:",
                "Synthetic regression result for tests.",
                "Best-fit complexity:",
                "A: O(n), B: O(n)",
                "Regression bullets:",
                "- 25% slowdown at max n",
                "Likely cause(s):",
                "- Extra work per element",
                "Evidence:",
                "- Runtime B consistently higher",
                "Optimization direction:",
                "- Reduce allocations",
                "Risk/edge cases:",
                "- Noisy benchmark runs",
            ]
        )

    analyzer.call_openai = fake_call_openai  # type: ignore[assignment]

    payload = {
        "language": "Python",
        "task": "Compare two implementations",
        "code": "print('hello')",
        "n": [100, 200, 400],
        "runtime_a": [1.0, 2.0, 4.0],
        "runtime_b": [1.1, 2.3, 5.0],
        "memory_a": [2.0, 2.1, 2.2],
        "memory_b": [2.1, 2.3, 2.6],
        "fit": {
            "a_best_fit": "O(n)",
            "a_confidence": 0.9,
            "b_best_fit": "O(n)",
            "b_confidence": 0.85,
        },
    }
    headers = {}
    if os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true" and os.getenv(
        "BACKEND_API_KEY"
    ):
        headers["X-API-Key"] = os.environ["BACKEND_API_KEY"]

    response = client.post("/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "raw_model_text" in body
    assert body["computed"]["slowdown_at_max_pct"] == 25.0
