from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import validate_required_openai_env
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_required_openai_env()
    init_db()
    yield


app = FastAPI(title="perf-copilot-api", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
