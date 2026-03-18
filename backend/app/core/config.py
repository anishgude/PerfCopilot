from __future__ import annotations

import os


def validate_required_openai_env() -> None:
    required = ["OPENAI_API_KEY", "OPENAI_MODEL"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variable(s): {names}. "
            "Set them before starting the backend."
        )
