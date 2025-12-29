/**
 * Application principale - Gestion de l'interface utilisateur
 */

// --- 1. SÉLECTION DES ÉLÉMENTS DU DOM ---
// On utilise les IDs définis dans ton nouveau index.html
const sequenceInput = document.getElementById('sequence');      
const seqLengthDisplay = document.getElementById('length');     
const seqValidDisplay = document.getElementById('valid');       
const foldBtn = document.getElementById('foldBtn');

const statusCard = document.getElementById('statusCard');       
const viewerSection = document.getElementById('viewerSection'); 
const jobIdDisplay = document.getElementById('jobId');          
const statusBadge = document.getElementById('statusBadge');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Contrôles du visualiseur 3D
const stepSlider = document.getElementById('stepSlider');
const stepLabel = document.getElementById('stepLabel');
const playBtn = document.getElementById('playBtn');

// --- 2. ÉTAT DE L'APPLICATION ---
let currentJobId = null;
let viewer = null;      // Instance 3Dmol
let jobResults = null;  // Données du job
let isPlaying = false;  // État de l'animation

// --- 3. LOGIQUE DE VALIDATION ---
sequenceInput.addEventListener('input', () => {
    const sequence = cleanSequence(sequenceInput.value);
    const length = sequence.length;
    
    seqLengthDisplay.textContent = `Longueur: ${length} aa`;
    
    const isValid = validateSequence(sequence);
    
    if (length === 0) {
        seqValidDisplay.textContent = '';
        seqValidDisplay.className = 'badge';
        foldBtn.disabled = true;
    } else if (isValid && length >= 10 && length <= 1000) {
        seqValidDisplay.textContent = '✓ Valide';
        seqValidDisplay.className = 'badge valid';
        foldBtn.disabled = false;
    } else {
        seqValidDisplay.textContent = '✗ Invalide';
        seqValidDisplay.className = 'badge invalid';
        foldBtn.disabled = true;
    }
});

// --- 4. LANCEMENT DU FOLDING ---
foldBtn.addEventListener('click', async () => {
    const sequence = cleanSequence(sequenceInput.value);
    
    // Reset UI
    foldBtn.disabled = true;
    foldBtn.textContent = '⏳ Lancement...';
    viewerSection.classList.remove('show'); 
    statusCard.classList.add('show');       
    
    try {
        // Appel API
        const response = await apiClient.foldProtein(sequence);
        currentJobId = response.job_id;
        
        // Mise à jour Status
        jobIdDisplay.textContent = currentJobId;
        statusBadge.textContent = 'En cours';
        statusBadge.className = 'badge processing';
        
        // Démarrer le polling (vérification régulière)
        await apiClient.pollStatus(currentJobId, updateProgress);
        
        // Une fois fini, on charge tout
        await loadResults(currentJobId);
        
    } catch (error) {
        console.error(error);
        statusBadge.textContent = 'Échec';
        statusBadge.className = 'badge invalid';
        foldBtn.disabled = false;
        foldBtn.textContent = '🚀 Lancer le repliement';
        alert("Erreur: " + error.message);
    }
});

function updateProgress(status) {
    const percent = (status.progress / status.total_steps) * 100;
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `Étape ${status.progress}/${status.total_steps}`;
}

// --- 5. GESTION DES RÉSULTATS & VISUALISATION ---
async function loadResults(jobId) {
    try {
        const results = await apiClient.getResults(jobId);
        jobResults = results;
        
        statusBadge.textContent = '✓ Terminé';
        statusBadge.className = 'badge completed';
        
        // Initialiser le visualiseur 3Dmol s'il n'existe pas encore
        if (!viewer) {
            viewer = $3Dmol.createViewer(document.getElementById('mol-viewer'), {
                backgroundColor: 'white'
            });
        }
        
        viewerSection.classList.add('show');
        
        // Configurer le slider pour naviguer dans les étapes
        stepSlider.max = results.steps.length - 1;
        stepSlider.value = results.steps.length - 1;
        
        // Charger la dernière étape (structure finale)
        loadStep(results.steps.length - 1);
        
        // Réactiver le bouton
        foldBtn.disabled = false;
        foldBtn.textContent = '🚀 Lancer le repliement';
        
        // Scroll vers le bas pour voir le résultat
        viewerSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error("Erreur chargement résultats", error);
    }
}

// Charge une étape spécifique dans le visualiseur
async function loadStep(index) {
    if (!jobResults) return;
    
    const step = jobResults.steps[index];
    stepLabel.textContent = `Etape ${index + 1}/${jobResults.steps.length}`;
    
    try {
        // Récupère le contenu du fichier PDB via l'API
        const pdbData = await apiClient.fetchPDB(step.pdb_url);
        
        viewer.clear();
        viewer.addModel(pdbData, "pdb");
        viewer.setStyle({}, {cartoon: {color: 'spectrum'}});
        viewer.zoomTo();
        viewer.render();
    } catch (e) {
        console.error("Erreur affichage PDB", e);
    }
}

// --- 6. CONTRÔLES DU PLAYER (Slider & Play) ---
stepSlider.addEventListener('input', (e) => {
    // Si on bouge le slider manuellement, on arrête l'animation auto
    isPlaying = false; 
    playBtn.textContent = '▶';
    loadStep(parseInt(e.target.value));
});

playBtn.addEventListener('click', () => {
    isPlaying = !isPlaying;
    playBtn.textContent = isPlaying ? '⏸' : '▶';
    if (isPlaying) animate();
});

function animate() {
    if (!isPlaying) return;
    
    let next = parseInt(stepSlider.value) + 1;
    if (next >= jobResults.steps.length) next = 0; // Boucle au début
    
    stepSlider.value = next;
    loadStep(next);
    
    setTimeout(animate, 500); // Vitesse de l'animation (500ms)
}

// --- 7. UTILITAIRES ---
function cleanSequence(seq) { 
    return seq.toUpperCase().replace(/[^A-Z]/g, ''); 
}

function validateSequence(seq) { 
    return /^[ACDEFGHIKLMNPQRSTVWY]+$/.test(seq); 
}

console.log('🧬 App JS loaded & linked to DOM');