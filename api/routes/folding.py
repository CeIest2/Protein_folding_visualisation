from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
import uuid
from pathlib import Path
import json

from api.services.fold_engine import run_folding

router = APIRouter()

class FoldRequest(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=1000)
    job_id: str | None = None
    
    @field_validator('sequence')
    def validate_sequence(cls, v):
        v = v.upper().replace(" ", "").replace("\n", "")
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        if not all(char in valid_aa for char in v):
            raise ValueError("Séquence invalide")
        return v

jobs_status = {}

@router.post("/fold")
async def fold_protein(request: FoldRequest, background_tasks: BackgroundTasks):
    job_id = request.job_id or str(uuid.uuid4())[:8]
    output_dir = Path(f"data/outputs/{job_id}")
    
    if output_dir.exists():
        return {"job_id": job_id, "status": "exists", "message": "Job existe déjà"}
    
    jobs_status[job_id] = {"status": "processing", "progress": 0, "total_steps": 8}
    background_tasks.add_task(run_folding, request.sequence, job_id, jobs_status)
    
    return {"job_id": job_id, "status": "processing", "message": "Folding démarré"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id in jobs_status:
        return {"job_id": job_id, **jobs_status[job_id]}
    
    metadata_path = Path(f"data/outputs/{job_id}/metadata.json")
    if metadata_path.exists():
        return {"job_id": job_id, "status": "completed", "progress": 8, "total_steps": 8}
    
    raise HTTPException(status_code=404, detail="Job introuvable")

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    metadata_path = Path(f"data/outputs/{job_id}/metadata.json")
    
    if not metadata_path.exists():
        if job_id in jobs_status and jobs_status[job_id]["status"] == "processing":
            return {"job_id": job_id, "sequence": "", "status": "processing", "steps": None}
        raise HTTPException(status_code=404, detail="Résultats introuvables")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    steps = [
        {
            "step": s["step"],
            "pdb_url": f"/data/outputs/{job_id}/{s['pdb_file']}",
            "avg_plddt": s["avg_plddt"],
            "plddt_per_residue": s["plddt_per_residue"]
        }
        for s in metadata["steps"]
    ]
    
    return {"job_id": job_id, "sequence": metadata["sequence"], "status": "completed", "steps": steps}