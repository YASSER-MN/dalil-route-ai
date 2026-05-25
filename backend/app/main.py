from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin, ask, feedback
from app.config import settings
from app.security.rate_limit import limiter

app = FastAPI(title="Dalil Route AI", version="1.0")

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
