"""Scenario FP&A API — application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth_router, budgets_router, scenarios_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Scenario FP&A API",
    version="1.0.0",
    description="Budget vs actuals and what-if scenario modelling for finance planning.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(budgets_router.router)
app.include_router(scenarios_router.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}
