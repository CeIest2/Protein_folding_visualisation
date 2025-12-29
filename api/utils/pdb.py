import numpy as np
from Bio.PDB import Structure, Model, Chain, Residue, Atom, PDBIO

def save_pdb(positions: np.ndarray, output_path: str, sequence: str):
    structure = Structure.Structure("ESMFold")
    model     = Model.Model(0)
    structure.add(model)
    chain     = Chain.Chain("A")
    model.add(chain)
    
    atom_names = ["N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "OG", "SG", "OD", "ND", "OE"]
    aa_map = {
        'A':'ALA', 'C':'CYS', 'D':'ASP', 'E':'GLU', 'F':'PHE', 'G':'GLY',
        'H':'HIS', 'I':'ILE', 'K':'LYS', 'L':'LEU', 'M':'MET', 'N':'ASN',
        'P':'PRO', 'Q':'GLN', 'R':'ARG', 'S':'SER', 'T':'THR', 'V':'VAL',
        'W':'TRP', 'Y':'TYR'
    }

    for i, aa in enumerate(sequence):
        res_name = aa_map.get(aa, "UNK")
        residue = Residue.Residue((' ', i+1, ' '), res_name, i+1)
        
        for j, atom_name in enumerate(atom_names):
            if j < positions.shape[1]:
                coords = positions[i, j]
                if np.sum(np.abs(coords)) > 1e-3: 
                    atom = Atom.Atom(atom_name, coords, 0.0, 1.0, " ", f" {atom_name:<3}", j+1, atom_name[0])
                    residue.add(atom)
        chain.add(residue)

    io = PDBIO()
    io.set_structure(structure)
    io.save(str(output_path))