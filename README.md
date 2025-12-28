# 🧬 Protein Folding Visualizer

Visualisation interactive du processus de repliement protéique avec ESMFold.

## 📋 Prérequis

- Docker avec support GPU (NVIDIA Docker)
- NVIDIA GPU avec CUDA 11.8+
- WSL2 (si sous Windows)

## 🚀 Démarrage rapide

### 1. Structure du projet

Créez la structure suivante :

```
protein-folding-viz/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── folding.py
│   └── services/
│       ├── __init__.py
│       └── fold_engine.py
├── webapp/
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── api-client.js
│       └── app.js
└── data/
    └── outputs/
```

### 2. Construction de l'image Docker

```bash
# Dans le dossier racine du projet
docker-compose build
```

⏱️ **Attention** : La première construction prend 10-15 minutes car le modèle ESMFold (~15GB) est téléchargé.

### 3. Lancement du conteneur

```bash
docker-compose up
```

L'API sera accessible sur : **http://localhost:8000**

### 4. Tester l'API

#### Option A : Via l'interface web
Ouvrez votre navigateur : http://localhost:8000

#### Option B : Via curl
```bash
# Lancer un folding
curl -X POST http://localhost:8000/api/fold \
  -H "Content-Type: application/json" \
  -d '{"sequence": "MPGWFKKAWYGLASLLSFSSFILIIVALVVPHWLSGKILCQTGV"}'

# Récupérer le statut (remplacez JOB_ID)
curl http://localhost:8000/api/status/JOB_ID

# Récupérer les résultats
curl http://localhost:8000/api/results/JOB_ID
```

#### Option C : Via la documentation auto-générée
http://localhost:8000/docs

## 📁 Résultats

Les fichiers PDB générés sont sauvegardés dans :
```
data/outputs/
└── {job_id}/
    ├── metadata.json
    ├── step_0.pdb
    ├── step_1.pdb
    ├── ...
    └── step_7.pdb
```

## 🔍 Vérifications

### 1. Vérifier que CUDA fonctionne
```bash
docker exec -it protein-folding-viz python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```
Doit afficher : `CUDA: True`

### 2. Vérifier les logs
```bash
docker-compose logs -f
```

### 3. Health check
```bash
curl http://localhost:8000/health
```

## 🛠️ Dépannage

### Erreur : "could not select device driver"
Vérifiez que NVIDIA Docker est installé :
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Erreur : "Port 8000 already in use"
Changez le port dans `docker-compose.yml` :
```yaml
ports:
  - "8001:8000"  # Au lieu de 8000:8000
```

### Le modèle se télécharge à chaque démarrage
Le cache Hugging Face devrait persister, mais si ce n'est pas le cas, ajoutez un volume :
```yaml
volumes:
  - ~/.cache/huggingface:/root/.cache/huggingface
```

## 📊 Performance attendue

Pour une protéine de 232 acides aminés :
- **Temps de calcul** : ~20-40 secondes (selon GPU)
- **Recycles générés** : 8 étapes
- **Taille des PDB** : ~50-100 KB chacun

## 🔄 Redémarrage

```bash
# Arrêter
docker-compose down

# Redémarrer
docker-compose up

# Reconstruire si modifications du code
docker-compose up --build
```

## 🧹 Nettoyage

```bash
# Supprimer les conteneurs
docker-compose down

# Supprimer les images
docker-compose down --rmi all

# Supprimer les volumes
docker-compose down -v
```

## 🎯 Prochaines étapes

- ✅ **Étape 1** : Setup Docker + API minimale (TERMINÉE)
- 🔄 **Étape 2** : Extraction complète des données (pLDDT, etc.)
- 📊 **Étape 3** : API complète avec tous les endpoints
- 🎨 **Étape 4** : Visualisation 3D avec 3DMol.js
- 🎮 **Étape 5** : Contrôles interactifs (slider, play/pause)
- 🌈 **Étape 6** : Mode "Confidence coloring"

## 📝 Notes pour l'intégration Angular

Le fichier `webapp/js/api-client.js` est conçu pour être facilement porté en TypeScript/Angular. 

Structure Angular recommandée :
```typescript
// protein-folding.service.ts
@Injectable({ providedIn: 'root' })
export class ProteinFoldingService {
  constructor(private http: HttpClient) {}
  // Reprendre les méthodes de api-client.js
}
```

## 📄 Licence

MIT