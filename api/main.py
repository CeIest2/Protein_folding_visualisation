from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os

from api.routes.folding import router as folding_router
from api.services.fold_engine import engine

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
WEBAPP_DIR = BASE_DIR / "webapp"

DATA_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    engine.load()
    yield
    # Arrêt
    engine.unload()

app = FastAPI(title="Protein Folding API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(folding_router, prefix="/api", tags=["folding"])


app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

if not WEBAPP_DIR.exists():
    raise RuntimeError(f"❌ Le dossier webapp est introuvable ici : {WEBAPP_DIR}")

app.mount("/", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")