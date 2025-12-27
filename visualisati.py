import os

# Paramètres
PDB_FILE = "CP2D7_HUMAN.pdb"
HTML_FILE = "visu_finale.html"

def create_standalone_html(pdb_path, output_path):
    if not os.path.exists(pdb_path):
        print(f"❌ Erreur : Le fichier {pdb_path} n'existe pas. Lance d'abord la génération.")
        return

    # 1. On lit le PDB
    with open(pdb_path, "r") as f:
        pdb_content = f.read()

    # 2. On nettoie le contenu pour éviter les bugs de guillemets dans le JS
    pdb_content_safe = pdb_content.replace("`", "").replace("\\", "\\\\")

    # 3. Le Template HTML (Sans jQuery, Pur JavaScript)
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Structure ESMFold : {pdb_path}</title>
    <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    <style>
        html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }}
        #viewer_container {{ width: 100%; height: 100%; position: relative; }}
        #overlay {{
            position: absolute; top: 10px; left: 10px; z-index: 10;
            background: rgba(255, 255, 255, 0.9); padding: 10px;
            border-radius: 4px; font-family: sans-serif;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div id="overlay">
        <strong>Protéine :</strong> {pdb_path}<br>
        <small>Utilise la souris pour tourner, molette pour zoomer.</small>
    </div>
    
    <div id="viewer_container"></div>

    <script>
        // On attend que la page soit chargée (Version sans jQuery)
        document.addEventListener("DOMContentLoaded", function() {{
            
            // 1. Initialisation
            let element = document.getElementById("viewer_container");
            let config = {{ backgroundColor: "white" }};
            
            // Création du viewer
            let viewer = $3Dmol.createViewer(element, config);

            // 2. Injection des données PDB
            let pdbData = `{pdb_content_safe}`;
            
            viewer.addModel(pdbData, "pdb");
            
            // 3. Style (Cartoon + Couleur arc-en-ciel)
            viewer.setStyle({{cartoon: {{color: 'spectrum'}}}});
            
            // 4. Rendu
            viewer.zoomTo();
            viewer.render();
            
            // Animation de rotation douce (optionnel, décommenter pour activer)
            // viewer.spin("y", 0.5);
        }});
    </script>
</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_template)
    
    print(f"✅ Page Web générée : {output_path}")
    print(f"👉 Ouvre ce fichier avec : explorer.exe {output_path}")

if __name__ == "__main__":
    create_standalone_html(PDB_FILE, HTML_FILE)