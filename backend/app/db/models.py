from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    benchmark_json: Mapped[str] = mapped_column(Text, nullable=False)
    raw_model_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    slowdown_at_max_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    slowdown_at_mid_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_growth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    a_best_fit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    b_best_fit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
