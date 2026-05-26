from dotenv import load_dotenv
load_dotenv()

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin, ask, feedback
from app.api.ask import get_generator, get_retriever, get_translator
from app.config import settings
from app.security.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Warming up models...", flush=True)
    t0 = time.time()
    get_translator()
    get_retriever()
    get_generator()
    print(f"Warmup complete in {time.time() - t0:.1f}s", flush=True)
    yield


app = FastAPI(title="Dalil Route AI", version="1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask.router)
app.include_router(feedback.router)
app.include_router(admin.router)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "dalil-route"}
