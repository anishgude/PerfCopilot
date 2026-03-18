from __future__ import annotations

import json

from app.schemas.benchmark import BenchmarkPayload


def _series(name: str, values: list[float] | None) -> str:
    if values is None:
        return f"{name}: N/A"
    return f"{name}: {json.dumps(values)}"


def build_analysis_prompt(payload: BenchmarkPayload) -> str:
    benchmark_b = "Not provided"
    if payload.runtime_b is not None or payload.memory_b is not None:
        benchmark_b = "\n".join(
            [
                _series("Runtime B", payload.runtime_b),
                _series("Memory B", payload.memory_b),
            ]
        )

    return "\n".join(
        [
            "You are Perf Copilot, a performance analysis assistant.",
            "Return a concise diagnosis using these exact sections:",
            "Summary:",
            "Best-fit complexity:",
            "Regression bullets:",
            "Likely cause(s):",
            "Evidence:",
            "Optimization direction:",
            "Risk/edge cases:",
            "",
            f"Language: {payload.language}",
            f"Task: {payload.task}",
            "Code:",
            payload.code,
            "",
            "Benchmark A:",
            f"Input sizes (n): {json.dumps(payload.n)}",
            _series("Runtime A", payload.runtime_a),
            _series("Memory A", payload.memory_a),
            "",
            "Benchmark B:",
            benchmark_b,
            "",
            "Fit:",
            f"A best fit: {payload.fit.a_best_fit} ({payload.fit.a_confidence:.2f})",
            (
                "B best fit: "
                f"{payload.fit.b_best_fit or 'Unknown'} "
                f"({(payload.fit.b_confidence or 0.0):.2f})"
            ),
            "",
            (
                "Be concrete about regressions, scaling, likely causes, and "
                "practical optimizations."
            ),
        ]
    )
