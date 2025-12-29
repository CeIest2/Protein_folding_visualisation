from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager # Nouvel import
import os

from api.routes.folding import router as folding_router
from api.services.fold_engine import engine # Import du singleton

# Gestion du cycle de vie (Démarrage / Arrêt)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Au démarrage : on pré-charge le modèle
    engine.load()
    yield
    # À l'arrêt : on nettoie la mémoire
    engine.unload()

app = FastAPI(
    title="Protein Folding Visualization API",
    description="API pour la prédiction et visualisation du repliement protéique avec ESMFold",
    version="1.0.0",
    lifespan=lifespan # Ajout du lifespan ici
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")
app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(folding_router, prefix="/api", tags=["folding"])

@app.get("/")
async def root():
    return FileResponse("webapp/index.html")

@app.get("/health")
async def health_check():
    import torch # Import propre
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available()
    }