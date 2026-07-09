from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, SessionLocal, engine
from .routers import airlines, carbon_credits, certificates, compliance, dashboard, feedstock, production
from .seed.mock_data import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title="SAF Monitoring System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedstock.router)
app.include_router(production.router)
app.include_router(certificates.router)
app.include_router(carbon_credits.router)
app.include_router(airlines.router)
app.include_router(compliance.router)
app.include_router(dashboard.router)
