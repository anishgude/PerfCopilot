from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ComplexityLabel = Literal[
    "O(1)",
    "O(log n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(2^n)",
    "Unknown",
]


class FitSummary(BaseModel):
    a_best_fit: ComplexityLabel = "Unknown"
    a_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    b_best_fit: ComplexityLabel | None = "Unknown"
    b_confidence: float | None = Field(default=0.0, ge=0.0, le=1.0)


class BenchmarkPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    n: list[int] = Field(..., min_length=1)
    runtime_a: list[float] = Field(..., min_length=1)
    runtime_b: list[float] | None = None
    memory_a: list[float] | None = None
    memory_b: list[float] | None = None
    fit: FitSummary

    @model_validator(mode="after")
    def validate_lengths(self) -> "BenchmarkPayload":
        expected = len(self.n)
        series = {
            "runtime_a": self.runtime_a,
            "runtime_b": self.runtime_b,
            "memory_a": self.memory_a,
            "memory_b": self.memory_b,
        }
        for name, values in series.items():
            if values is not None and len(values) != expected:
                raise ValueError(f"{name} must have the same length as n")
        if self.runtime_b is not None and self.fit.b_best_fit is None:
            self.fit.b_best_fit = "Unknown"
        return self


class ComputedMetrics(BaseModel):
    slowdown_at_mid_pct: float | None = None
    slowdown_at_max_pct: float | None = None
    memory_growth_at_max_pct: float | None = None
    max_n: int | None = None
    mid_n: int | None = None


class ParsedDiagnosis(BaseModel):
    summary: str | None = None
    best_fit_complexity: str | None = None
    regression_bullets: list[str] = Field(default_factory=list)
    likely_causes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    optimization_direction: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    raw_model_text: str
    parsed: ParsedDiagnosis | None = None
    computed: ComputedMetrics
    fit: FitSummary


class HealthResponse(BaseModel):
    status: str


class UploadAnalyzeResponse(BaseModel):
    run_id: int
    status: str
    computed: ComputedMetrics | None = None
    parsed: ParsedDiagnosis | None = None
    raw_model_text: str | None = None
    error_message: str | None = None


class RunListItem(BaseModel):
    id: int
    created_at: datetime
    title: str | None
    language: str
    status: str
    slowdown_at_max_pct: float | None = None
    a_best_fit: str | None = None
    b_best_fit: str | None = None


class RunDetailResponse(BaseModel):
    id: int
    created_at: datetime
    title: str | None
    language: str
    task: str
    code: str
    benchmark_json: dict
    raw_model_text: str | None = None
    parsed_output_json: dict | None = None
    slowdown_at_max_pct: float | None = None
    slowdown_at_mid_pct: float | None = None
    memory_growth_pct: float | None = None
    a_best_fit: str | None = None
    b_best_fit: str | None = None
    status: str
    error_message: str | None = None
