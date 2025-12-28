import torch
from transformers import AutoTokenizer, EsmForProteinFolding
import numpy as np
import json
from pathlib import Path
import traceback

def run_folding(sequence: str, job_id: str, jobs_status: dict):
    """
    Exécute le repliement protéique avec ESMFold et sauvegarde tous les recycles
    
    Args:
        sequence: Séquence d'acides aminés
        job_id: Identifiant unique du job
        jobs_status: Dictionnaire partagé pour mettre à jour le statut
    """
    output_dir = Path(f"data/outputs/{job_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"🚀 Démarrage du folding pour job {job_id}")
        print(f"   Séquence : {sequence[:50]}... (longueur: {len(sequence)})")
        
        # 1. Chargement du modèle
        jobs_status[job_id]["progress"] = 1
        model_name = "facebook/esmfold_v1"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = EsmForProteinFolding.from_pretrained(model_name, low_cpu_mem_usage=True)
        
        # Vérifier si CUDA est disponible
        print(f" gpu {torch.cuda.is_available()}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Device: {device}")
        
        if device == "cuda":
            model = model.cuda().to(torch.bfloat16)
        model.eval()
        
        jobs_status[job_id]["progress"] = 2
        
        # 2. Inférence avec capture de tous les recycles
        print("🧠 Calcul du repliement...")
        with torch.no_grad():
            inputs = tokenizer([sequence], return_tensors="pt", add_special_tokens=False)
            if device == "cuda":
                inputs = {key: val.cuda() for key, val in inputs.items()}
            
            outputs = model(**inputs)
        
        # 3. Extraction des données
        # outputs.positions shape: [num_recycles, batch, seq_len, 14, 3]
        # outputs.plddt shape: [batch, seq_len]
        
        positions_all = outputs.positions.detach().float().cpu().numpy()
        plddt = outputs.plddt[0].detach().float().cpu().numpy()  # [seq_len]
        
        num_recycles = positions_all.shape[0]
        print(f"   Recycles capturés : {num_recycles}")
        print(f"   Shape positions : {positions_all.shape}")
        print(f"   pLDDT moyen : {plddt.mean():.2f}")
        
        jobs_status[job_id]["total_steps"] = num_recycles
        
        # 4. Génération des PDB pour chaque recycle
        metadata = {
            "job_id": job_id,
            "sequence": sequence,
            "num_recycles": num_recycles,
            "avg_plddt_global": float(plddt.mean()),
            "steps": []
        }
        
        for recycle_idx in range(num_recycles):
            jobs_status[job_id]["progress"] = 3 + recycle_idx
            
            # Extraire les positions pour ce recycle
            # positions shape pour ce recycle: [seq_len, 14, 3]
            positions = positions_all[recycle_idx, 0]  # [0] pour le batch
            
            # Générer le fichier PDB
            pdb_filename = f"step_{recycle_idx}.pdb"
            pdb_path = output_dir / pdb_filename
            
            write_pdb(positions, pdb_path, sequence)
            
            # Métadonnées pour ce step
            metadata["steps"].append({
                "step": recycle_idx,
                "pdb_file": pdb_filename,
                "avg_plddt": float(plddt.mean()),
                "plddt_per_residue": plddt.tolist()
            })
            
            print(f"   ✓ Step {recycle_idx}/{num_recycles-1} généré")
        
        # 5. Sauvegarder les métadonnées
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Mettre à jour le statut final
        jobs_status[job_id] = {
            "status": "completed",
            "progress": num_recycles,
            "total_steps": num_recycles
        }
        
        print(f"🎉 Folding complété pour job {job_id}")
        
    except Exception as e:
        print(f"❌ Erreur lors du folding : {str(e)}")
        traceback.print_exc()
        jobs_status[job_id] = {
            "status": "failed",
            "error": str(e)
        }

def write_pdb(positions: np.ndarray, output_path: Path, sequence: str):
    """
    Écrit un fichier PDB à partir des positions atomiques
    
    Args:
        positions: Array numpy [seq_len, 14, 3] avec les coordonnées
        output_path: Chemin de sortie
        sequence: Séquence pour avoir les noms de résidus
    """
    # Mapping des acides aminés en code 3 lettres
    aa_mapping = {
        'A': 'ALA', 'C': 'CYS', 'D': 'ASP', 'E': 'GLU',
        'F': 'PHE', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
        'K': 'LYS', 'L': 'LEU', 'M': 'MET', 'N': 'ASN',
        'P': 'PRO', 'Q': 'GLN', 'R': 'ARG', 'S': 'SER',
        'T': 'THR', 'V': 'VAL', 'W': 'TRP', 'Y': 'TYR'
    }
    
    # Noms des atomes dans le format atom14 d'ESMFold
    # Les 4 premiers sont le backbone (N, CA, C, O)
    atom_names = ["N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "OG", "SG", "OD", "ND", "OE"]
    
    pdb_lines = []
    atom_serial = 1
    
    for res_idx, res_atoms in enumerate(positions):
        # Obtenir le nom du résidu
        aa_letter = sequence[res_idx] if res_idx < len(sequence) else 'X'
        res_name = aa_mapping.get(aa_letter, 'UNK')
        
        # Écrire les atomes (au moins le backbone)
        for atom_idx in range(min(4, len(res_atoms))):  # Au moins N, CA, C, O
            coords = res_atoms[atom_idx]
            
            # Ignorer les atomes non définis (0,0,0)
            if np.sum(np.abs(coords)) < 1e-3:
                continue
            
            x, y, z = coords
            atom_name = atom_names[atom_idx]
            
            # Format PDB standard
            pdb_line = (
                f"ATOM  {atom_serial:5d}  {atom_name:<3s} {res_name:>3s} A{res_idx+1:4d}    "
                f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {atom_name[0]:>1s}"
            )
            pdb_lines.append(pdb_line)
            atom_serial += 1
    
    pdb_lines.append("END")
    
    # Écrire le fichier
    with open(output_path, "w") as f:
        f.write("\n".join(pdb_lines))