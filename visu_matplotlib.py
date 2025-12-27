import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

PDB_FILE = "CP2D7_HUMAN.pdb"

def parse_pdb_backbone(filename):
    coords = []
    # On lit le fichier ligne par ligne
    with open(filename, 'r') as f:
        for line in f:
            # On cherche les lignes qui décrivent un atome
            if line.startswith("ATOM"):
                # On veut uniquement le Carbone Alpha (" CA ") pour alléger le plot
                # C'est le point central de chaque acide aminé
                atom_name = line[12:16].strip()
                if atom_name == "CA":
                    # Format PDB fixe : X=30-38, Y=38-46, Z=46-54
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append([x, y, z])
    return np.array(coords)

def plot_protein(coords):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Extraction des axes
    xs = coords[:, 0]
    ys = coords[:, 1]
    zs = coords[:, 2]

    # 1. Tracer la ligne (le squelette)
    # On utilise un dégradé de couleur (cmap) pour voir le sens (Début -> Fin)
    # C'est une astuce pour simuler le "N-ter vers C-ter"
    N = len(xs)
    for i in range(N - 1):
        ax.plot(
            xs[i:i+2], ys[i:i+2], zs[i:i+2], 
            color=plt.cm.jet(i / N), # Couleur changeante
            linewidth=2, 
            alpha=0.8
        )

    # 2. (Optionnel) Ajouter des points pour marquer les résidus
    # ax.scatter(xs, ys, zs, s=10, c=range(N), cmap='jet', depthshade=True)

    # Esthétique
    ax.set_title(f"Structure de {PDB_FILE} (C-alpha trace)\nBleu = Début, Rouge = Fin")
    ax.set_xlabel('X (Å)')
    ax.set_ylabel('Y (Å)')
    ax.set_zlabel('Z (Å)')
    
    # Masquer les grilles pour faire plus "pro"
    ax.grid(False)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    print("affichage du plot...")
    plt.show()

if __name__ == "__main__":
    data = parse_pdb_backbone(PDB_FILE)
    if len(data) == 0:
        print("❌ Erreur : Aucun atome 'CA' trouvé. Vérifie ton fichier PDB.")
    else:
        print(f"✅ {len(data)} résidus extraits.")
        plot_protein(data)