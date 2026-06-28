"""FastAPI-Einstieg: CORS, Router, Startup (DB + Seed)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    anlagen,
    auth,
    finanzaemter,
    gaap,
    health,
    kontennachweise,
    mapping,
    odoo,
    stammdaten,
    taxonomie,
    uebermittlung,
    validierung,
    wirtschaftsjahr,
)
from app.seed import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # DB-Tabellen anlegen + Seed (Super-Admin, Odoo-Config, 4 WJ) — idempotent.
    init_db()
    yield


app = FastAPI(title="eBilanz Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(odoo.router)
app.include_router(taxonomie.router)
app.include_router(finanzaemter.router)
app.include_router(wirtschaftsjahr.router)
app.include_router(mapping.router)
app.include_router(gaap.router)
app.include_router(anlagen.router)
app.include_router(kontennachweise.router)
app.include_router(validierung.router)
app.include_router(uebermittlung.router)
app.include_router(stammdaten.router)
