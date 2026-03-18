from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("BACKEND_API_KEY")
    auth_enabled = os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
    if auth_enabled and expected and x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
