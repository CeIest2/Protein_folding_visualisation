import os
from pathlib import Path

# Chemins absolus basés sur la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

# Paramètres du modèle
MODEL_NAME = "facebook/esmfold_v1"
DEVICE = "cuda"  # ou logique automatique

# Paramètres de validation
MIN_SEQ_LEN = 10
MAX_SEQ_LEN = 600

# Création automatique des dossiers au démarrage
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)