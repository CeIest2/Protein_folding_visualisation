
import torch
from transformers import AutoTokenizer, EsmForProteinFolding
import os
import sys
import numpy as np

# --- DONNÉES ---
SEQUENCE = "MPGWFKKAWYGLASLLSFSSFILIIVALVVPHWLSGKILCQTGVDLVNATDRELVKFIGDIYYGLFRGCKVRQCGLGGRQSQFTIFPHLVKELNAGLHVMILLLLFLALALALVSMGFAILNMIQVPYRAVSGPGGICLWNVLAGGVVALAIASFVAAVKFHDLTERIANFQEKLFQFVVVEEQYEESFWICVASASAHAANLVVVAISQIPLPEIKTKIEEATVTAEDILY"
ID = "CP2D7_HUMAN"
FILENAME = f"{ID}.pdb"

def run_fix():
    print(f"🚀 Démarrage pour {ID}...")
    
    # 1. Chargement
    model_name = "facebook/esmfold_v1"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = EsmForProteinFolding.from_pretrained(model_name, low_cpu_mem_usage=True)
    model = model.cuda().to(torch.bfloat16)
    model.eval()

    # 2. Inférence
    print("🧠 Calcul du repliement...")
    with torch.no_grad():
        inputs = tokenizer([SEQUENCE], return_tensors="pt", add_special_tokens=False)
        inputs = {key: val.cuda() for key, val in inputs.items()}
        outputs = model(**inputs)

    # 3. Correction des dimensions (Le FIX est ici)
    # Tes logs disent : [8, 1, 232, 14, 3] -> (Recycles, Batch, Seq, Atoms, XYZ)
    # On prend [-1] (le dernier recycle, le plus précis)
    # Puis [0] (le premier élément du batch)
    final_pos = outputs.positions[-1, 0].detach().float().cpu().numpy()
    
    # Maintenant final_pos a la forme (232, 14, 3) -> (Seq, Atoms, XYZ)
    print(f"✅ Dimensions corrigées : {final_pos.shape} (Doit être [LONGUEUR, 14, 3])")

    # 4. Écriture PDB adaptée au format 'atom14'
    # Dans ce format réduit, l'ordre est généralement : N=0, CA=1, C=2, O=3
    atom_indices = [0, 1, 2, 3] 
    atom_names = ["N", "CA", "C", "O"]
    
    pdb_lines = []
    atom_serial = 1

    for i, res_atoms in enumerate(final_pos):
        # res_atoms est de taille (14, 3)
        for j, atom_idx in enumerate(atom_indices):
            coords = res_atoms[atom_idx] # [x, y, z]
            
            # Vérification que ce n'est pas un atome vide (0,0,0)
            if np.sum(np.abs(coords)) < 1e-3:
                continue

            x, y, z = coords
            
            pdb_lines.append(
                f"ATOM  {atom_serial:5d}  {atom_names[j]:<2s}  UNK A{i+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           {atom_names[j][0]}"
            )
            atom_serial += 1

    # 5. Sauvegarde
    with open(FILENAME, "w") as f:
        f.write("\n".join(pdb_lines))
        
    print(f"🎉 SUCCÈS TOTAL ! Fichier sauvegardé : {FILENAME}")
    print(f"👉 Taille du fichier : {os.path.getsize(FILENAME)} octets")

if __name__ == "__main__":
    run_fix()