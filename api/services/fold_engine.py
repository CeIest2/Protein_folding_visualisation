import torch
from transformers import AutoTokenizer, EsmForProteinFolding
import numpy as np
import json
from pathlib import Path
import traceback
import gc

# Imports Biopython
from Bio.PDB import Structure, Model, Chain, Residue, Atom, PDBIO

class FoldingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FoldingEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
            cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
        return cls._instance

    def load(self):
        if self.model is not None:
            return

        print(f"🏗️ Chargement du modèle ESMFold (Standard FP16)...")
        try:
            model_name = "facebook/esmfold_v1"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # On charge en FP16 pour économiser la VRAM (6 Go vs 12 Go)
            self.model = EsmForProteinFolding.from_pretrained(
                model_name, 
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            
            self.model.eval()
            print("✅ Modèle chargé en FP16.")
            
        except Exception as e:
            print(f"❌ Erreur critique lors du chargement du modèle : {e}")
            raise e

    def unload(self):
        if self.model is not None:
            print("🧹 Nettoyage de la mémoire GPU...")
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

    def predict(self, sequence: str):
        if self.model is None:
            self.load()

        with torch.no_grad():
            inputs = self.tokenizer([sequence], return_tensors="pt", add_special_tokens=False)
            
            if torch.cuda.is_available():
                device = next(self.model.parameters()).device
                inputs = {key: val.to(device) for key, val in inputs.items()}
                
                # --- CORRECTIF : AUTOCAST ---
                # Permet de mélanger Float16 (modèle) et Float32 (calculs internes)
                with torch.amp.autocast("cuda"):
                    return self.model(**inputs)
            else:
                return self.model(**inputs)

# Instance globale
engine = FoldingEngine()

def run_folding(sequence: str, job_id: str, jobs_status: dict):
    output_dir = Path(f"data/outputs/{job_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"🚀 Job {job_id}: Démarrage (seq len: {len(sequence)})")
        jobs_status[job_id]["progress"] = 1
        
        # 1. Inférence
        print(f"🧠 Job {job_id}: Inférence en cours...")
        outputs = engine.predict(sequence)
        jobs_status[job_id]["progress"] = 2
        
        # 2. Extraction des données
        # On repasse en float32 pour l'export Numpy pour éviter tout souci
        positions_all = outputs.positions.detach().float().cpu().numpy()
        plddt = outputs.plddt[0].detach().float().cpu().numpy().flatten()
        
        num_recycles = positions_all.shape[0]
        jobs_status[job_id]["total_steps"] = num_recycles
        
        metadata = {
            "job_id": job_id,
            "sequence": sequence,
            "num_recycles": num_recycles,
            "avg_plddt_global": float(plddt.mean()),
            "steps": []
        }
        jobs_status[job_id]["steps"] = []        
        # 3. Génération des fichiers PDB
        for recycle_idx in range(num_recycles):
            jobs_status[job_id]["progress"] = 3 + recycle_idx
            
            positions = positions_all[recycle_idx, 0]
            pdb_filename = f"step_{recycle_idx}.pdb"
            pdb_path = output_dir / pdb_filename
            
            save_pdb_biopython(positions, pdb_path, sequence)
            
            step_data = {
                "step": recycle_idx,
                "pdb_file": pdb_filename,
                "avg_plddt": float(plddt.mean()),
                "plddt_per_residue": [round(float(x), 2) for x in plddt.tolist()]
            }
            
            metadata["steps"].append(step_data)

            jobs_status[job_id]["steps"].append(step_data)
            
        # 4. Sauvegarde
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        jobs_status[job_id].update({
            "status": "completed",
            "progress": num_recycles,
            "total_steps": num_recycles
        })
        print(f"🎉 Job {job_id}: Terminé avec succès.")
        
    except Exception as e:
        print(f"❌ Job {job_id} échoué : {str(e)}")
        traceback.print_exc()
        jobs_status[job_id].update({
            "status": "failed",
            "error": str(e)
        })

def save_pdb_biopython(positions: np.ndarray, output_path: Path, sequence: str):
    structure = Structure.Structure("ESMFold")
    model = Model.Model(0)
    structure.add(model)
    chain = Chain.Chain("A")
    model.add(chain)
    
    atom_names = ["N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "OG", "SG", "OD", "ND", "OE"]
    
    aa_map = {
        'A':'ALA', 'C':'CYS', 'D':'ASP', 'E':'GLU', 'F':'PHE', 'G':'GLY',
        'H':'HIS', 'I':'ILE', 'K':'LYS', 'L':'LEU', 'M':'MET', 'N':'ASN',
        'P':'PRO', 'Q':'GLN', 'R':'ARG', 'S':'SER', 'T':'THR', 'V':'VAL',
        'W':'TRP', 'Y':'TYR'
    }

    for i, res_name_1 in enumerate(sequence):
        res_name_3 = aa_map.get(res_name_1, "UNK")
        residue = Residue.Residue((' ', i+1, ' '), res_name_3, i+1)
        
        has_atoms = False
        for atom_idx, atom_name in enumerate(atom_names):
            if atom_idx >= positions.shape[1]: 
                continue
                
            coords = positions[i, atom_idx]
            if np.sum(np.abs(coords)) < 1e-3:
                continue
                
            atom = Atom.Atom(
                name=atom_name,
                coord=coords,
                bfactor=0.0,
                occupancy=1.0,
                altloc=" ",
                fullname=f" {atom_name:<3}",
                serial_number=atom_idx+1,
                element=atom_name[0]
            )
            residue.add(atom)
            has_atoms = True
            
        if has_atoms:
            chain.add(residue)

    io = PDBIO()
    io.set_structure(structure)
    io.save(str(output_path))