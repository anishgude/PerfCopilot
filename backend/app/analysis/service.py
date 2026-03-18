from __future__ import annotations

import os
from typing import Any

import httpx

from app.analysis.parser import parse_diagnosis
from app.analysis.prompt_builder import build_analysis_prompt
from app.schemas.benchmark import AnalyzeResponse, BenchmarkPayload, ComputedMetrics

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class AnalyzerError(RuntimeError):
    """Raised when model analysis fails."""


def _percent_delta(old: float, new: float) -> float | None:
    if old == 0:
        return None
    return round(((new - old) / old) * 100.0, 2)


def compute_metrics(payload: BenchmarkPayload) -> ComputedMetrics:
    metrics = ComputedMetrics()
    if not payload.n:
        return metrics

    max_index = len(payload.n) - 1
    mid_index = len(payload.n) // 2
    metrics.max_n = payload.n[max_index]
    metrics.mid_n = payload.n[mid_index]

    if payload.runtime_b is not None:
        metrics.slowdown_at_max_pct = _percent_delta(
            payload.runtime_a[max_index],
            payload.runtime_b[max_index],
        )
        metrics.slowdown_at_mid_pct = _percent_delta(
            payload.runtime_a[mid_index],
            payload.runtime_b[mid_index],
        )

    if payload.memory_a is not None and payload.memory_b is not None:
        metrics.memory_growth_at_max_pct = _percent_delta(
            payload.memory_a[max_index],
            payload.memory_b[max_index],
        )

    return metrics


def _fallback_text(payload: BenchmarkPayload, metrics: ComputedMetrics) -> str:
    slowdown = (
        "N/A"
        if metrics.slowdown_at_max_pct is None
        else f"{metrics.slowdown_at_max_pct}%"
    )
    causes = [
        (
            "A heavier inner-loop or additional allocations are increasing "
            "per-element work."
        ),
        (
            "Scaling characteristics may be diverging as n grows, especially if "
            "benchmark B changes fit."
        ),
    ]
    fixes = [
        (
            "Profile hotspots at the largest input size and remove repeated work "
            "inside loops."
        ),
        (
            "Reduce temporary allocations and prefer streaming or in-place "
            "processing where safe."
        ),
    ]
    mid_slowdown = (
        f"{metrics.slowdown_at_mid_pct}%"
        if metrics.slowdown_at_mid_pct is not None
        else "N/A%"
    )
    lines = [
        "Summary:",
        f"Benchmark B shows a slowdown of {slowdown} at the largest input size.",
        "Best-fit complexity:",
        f"A: {payload.fit.a_best_fit}; B: {payload.fit.b_best_fit or 'Unknown'}",
        "Regression bullets:",
        f"- Midpoint slowdown: {mid_slowdown}",
        f"- Max slowdown: {slowdown}",
        "Likely cause(s):",
        *[f"- {cause}" for cause in causes],
        "Evidence:",
        f"- Input sizes analyzed: {payload.n}",
        f"- Runtime A: {payload.runtime_a}",
        f"- Runtime B: {payload.runtime_b if payload.runtime_b is not None else 'N/A'}",
        "Optimization direction:",
        *[f"- {fix}" for fix in fixes],
        "Risk/edge cases:",
        (
            "- Noisy microbenchmarks can overstate regressions; re-run with warmups "
            "and multiple trials."
        ),
    ]
    return "\n".join(lines)


async def call_openai(payload: BenchmarkPayload, prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return _fallback_text(payload, compute_metrics(payload))

    request_body: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You analyze benchmark deltas and return structured performance "
                    "diagnoses."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENAI_URL,
                headers=headers,
                json=request_body,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AnalyzerError(f"OpenAI request failed: {exc}") from exc

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AnalyzerError("Unexpected OpenAI response shape") from exc


async def analyze_payload(payload: BenchmarkPayload) -> AnalyzeResponse:
    prompt = build_analysis_prompt(payload)
    metrics = compute_metrics(payload)

    try:
        raw_text = await call_openai(payload, prompt)
    except AnalyzerError:
        raw_text = _fallback_text(payload, metrics)

    parsed = parse_diagnosis(raw_text)
    return AnalyzeResponse(
        raw_model_text=raw_text,
        parsed=parsed,
        computed=metrics,
        fit=payload.fit,
    )
