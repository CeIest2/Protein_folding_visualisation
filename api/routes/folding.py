# api/routes/folding.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import uuid
import json
import traceback
from pathlib import Path

from api.config import OUTPUT_DIR
from api.services.fold_engine import engine
from api.utils.pdb import save_pdb

router = APIRouter()

class FoldRequest(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=1000)

# --- LA NOUVELLE FONCTION RUN_FOLDING (Déplacée ici) ---
def process_folding_job(job_id: str, sequence: str):
    job_dir = OUTPUT_DIR / job_id
    status_file = job_dir / "status.json"
    
    try:
        # 1. Ecrire que ça démarre
        status_data = {"status": "processing", "progress": 0, "total_steps": 0}
        with open(status_file, "w") as f: json.dump(status_data, f)

        # 2. IA
        outputs = engine.predict(sequence)
        
        # 3. Traitement
        positions_all = outputs.positions.detach().float().cpu().numpy()
        plddt = outputs.plddt[0].detach().float().cpu().numpy().flatten()
        num_recycles = positions_all.shape[0]
        
        steps = []
        for i in range(num_recycles):
            # Mise à jour progression
            status_data.update({"progress": i + 1, "total_steps": num_recycles})
            with open(status_file, "w") as f: json.dump(status_data, f)
            
            # Sauvegarde PDB (Appel à notre nouveau fichier utils)
            pdb_name = f"step_{i}.pdb"
            save_pdb(positions_all[i, 0], job_dir / pdb_name, sequence)
            
            steps.append({
                "step": i, "pdb_url": f"/data/outputs/{job_id}/{pdb_name}",
                "avg_plddt": float(plddt.mean())
            })

        # 4. Finalisation (metadata.json = Job fini)
        final_meta = {
            "job_id": job_id, "sequence": sequence, 
            "status": "completed", "steps": steps
        }
        with open(job_dir / "metadata.json", "w") as f: json.dump(final_meta, f)
        
        # On supprime le status temporaire
        status_file.unlink(missing_ok=True)
        
    except Exception as e:
        traceback.print_exc()
        with open(status_file, "w") as f:
            json.dump({"status": "failed", "error": str(e)}, f)

# --- ROUTES ---

@router.post("/fold")
async def fold_protein(request: FoldRequest, tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    (OUTPUT_DIR / job_id).mkdir(parents=True, exist_ok=True)
    
    tasks.add_task(process_folding_job, job_id, request.sequence)
    return {"job_id": job_id, "status": "processing"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    job_dir = OUTPUT_DIR / job_id
    
    # 1. Si fini (metadata.json existe)
    if (job_dir / "metadata.json").exists():
        with open(job_dir / "metadata.json") as f: return json.load(f)
        
    # 2. Si en cours (status.json existe)
    if (job_dir / "status.json").exists():
        with open(job_dir / "status.json") as f: return {"job_id": job_id, **json.load(f)}
        
    raise HTTPException(404, "Job introuvable")

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    return await get_status(job_id) # Même logique maintenant