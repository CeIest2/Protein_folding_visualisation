# api/services/fold_engine.py
import torch
from transformers import AutoTokenizer, EsmForProteinFolding
from api.config import MODEL_NAME
import gc

class FoldingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FoldingEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
        return cls._instance

    def load(self):
        if self.model: return
        print(f"🏗️ Chargement de {MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = EsmForProteinFolding.from_pretrained(
            MODEL_NAME, 
            device_map="auto", 
            torch_dtype=torch.float16, 
            low_cpu_mem_usage=True
        )
        self.model.eval()

    def unload(self):
        if not self.model: return
        del self.model, self.tokenizer
        self.model = None
        torch.cuda.empty_cache()
        gc.collect()

    def predict(self, sequence: str):
        if not self.model: self.load()
        with torch.no_grad():
            inputs = self.tokenizer([sequence], return_tensors="pt", add_special_tokens=False)
            if torch.cuda.is_available():
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                with torch.amp.autocast("cuda"):
                    return self.model(**inputs)
            return self.model(**inputs)

# Instance globale
engine = FoldingEngine()