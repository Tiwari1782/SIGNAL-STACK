from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import FRONTEND_ORIGIN
from .db import query
from .routers.companies import router as companies_router
from .routers.interview import router as interview_router
from .routers.sources import router as sources_router
from .routers.crawler import router as crawler_router
from .routers.feed import router as feed_router
from .routers.briefs import router as briefs_router
from .routers.settings import router as settings_router
from .routers.jobs import router as jobs_router
from .routers.uploads import router as uploads_router

app = FastAPI(title="Signal Stack API")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, "*"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(companies_router)
app.include_router(interview_router)
app.include_router(sources_router)
app.include_router(crawler_router)
app.include_router(feed_router)
app.include_router(briefs_router)
app.include_router(settings_router)
app.include_router(jobs_router)
app.include_router(uploads_router)

@app.get("/")
def root():
    return {
        "status": "online",
        "name": "Signal Stack API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    query("SELECT 1")
    return {"ok": True}

@app.get("/job-runs")
def job_runs(limit: int = 50):
    return query("SELECT * FROM job_runs ORDER BY started_at DESC LIMIT %s", (limit,))
