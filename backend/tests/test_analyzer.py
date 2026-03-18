from app.analysis.parser import parse_diagnosis
from app.analysis.prompt_builder import build_analysis_prompt
from app.analysis.service import compute_metrics
from app.schemas.benchmark import BenchmarkPayload, FitSummary


def sample_payload() -> BenchmarkPayload:
    return BenchmarkPayload(
        language="Python",
        task="Compare list-based aggregation implementations.",
        code=(
            "def run(xs):\n"
            "    total = 0\n"
            "    for x in xs:\n"
            "        total += x\n"
            "    return total"
        ),
        n=[1000, 2000, 4000, 8000],
        runtime_a=[1.0, 2.0, 4.1, 8.0],
        runtime_b=[1.2, 2.5, 5.3, 10.4],
        memory_a=[3.0, 3.1, 3.2, 3.4],
        memory_b=[3.1, 3.5, 3.8, 4.4],
        fit=FitSummary(
            a_best_fit="O(n)",
            a_confidence=0.92,
            b_best_fit="O(n)",
            b_confidence=0.89,
        ),
    )


def test_compute_metrics() -> None:
    metrics = compute_metrics(sample_payload())
    assert metrics.slowdown_at_mid_pct == 29.27
    assert metrics.slowdown_at_max_pct == 30.0
    assert metrics.memory_growth_at_max_pct == 29.41
    assert metrics.max_n == 8000
    assert metrics.mid_n == 4000


def test_build_prompt_contains_sections() -> None:
    prompt = build_analysis_prompt(sample_payload())
    assert "Language: Python" in prompt
    assert "Benchmark A:" in prompt
    assert "Benchmark B:" in prompt
    assert "Best-fit complexity:" in prompt


def test_parse_diagnosis() -> None:
    raw = "\n".join(
        [
            "Summary:",
            "Runtime B regresses as input size grows.",
            "Best-fit complexity:",
            "A: O(n), B: O(n)",
            "Regression bullets:",
            "- 30% slowdown at max n",
            "Likely cause(s):",
            "- Extra allocations inside the loop",
            "Evidence:",
            "- Runtime B grows faster than A",
            "Optimization direction:",
            "- Reuse buffers",
            "Risk/edge cases:",
            "- Noise at small n",
        ]
    )
    parsed = parse_diagnosis(raw)
    assert parsed is not None
    assert parsed.summary == "Runtime B regresses as input size grows."
    assert parsed.regression_bullets == ["30% slowdown at max n"]
    assert parsed.likely_causes == ["Extra allocations inside the loop"]
