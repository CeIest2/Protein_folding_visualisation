from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routes.folding import router as folding_router
from contextlib import asynccontextmanager
from api.services.fold_engine import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.load()
    yield
    # À l'arrêt : on nettoie
    engine.unload()

app = FastAPI(
    title="Protein Folding Visualization API",
    description="API pour la prédiction et visualisation du repliement protéique avec ESMFold",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, spécifiez votre domaine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Routes API
app.include_router(folding_router, prefix="/api", tags=["folding"])

@app.get("/")
async def root():
    """Redirection vers la webapp de test"""
    return FileResponse("webapp/index.html")

@app.get("/health")
async def health_check():
    """Endpoint de santé pour Docker healthcheck"""
    return {
        "status": "healthy",
        "cuda_available": __import__("torch").cuda.is_available()
    }