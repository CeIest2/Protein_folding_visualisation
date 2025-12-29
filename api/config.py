from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

MODEL_NAME = "facebook/esmfold_v1"
DEVICE = "cuda"  

MIN_SEQ_LEN = 10
MAX_SEQ_LEN = 600

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)