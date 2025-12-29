/**
 * Application principale - Gestion de l'interface utilisateur
 */

// --- 1. SÉLECTION DES ÉLÉMENTS DU DOM ---
// On utilise les IDs définis dans ton nouveau index.html
const sequenceInput    = document.getElementById('sequence');      
const seqLengthDisplay = document.getElementById('length');     
const seqValidDisplay  = document.getElementById('valid');       
const foldBtn          = document.getElementById('foldBtn');

const statusCard    = document.getElementById('statusCard');       
const viewerSection = document.getElementById('viewerSection'); 
const jobIdDisplay  = document.getElementById('jobId');          
const statusBadge   = document.getElementById('statusBadge');
const progressFill  = document.getElementById('progressFill');
const progressText  = document.getElementById('progressText');

const stepSlider = document.getElementById('stepSlider');
const stepLabel  = document.getElementById('stepLabel');
const playBtn    = document.getElementById('playBtn');

let currentJobId = null;
let viewer       = null;      // Instance 3Dmol
let jobResults   = null;  // Données du job
let isPlaying    = false;  // État de l'animation

function calculateEstimatedTime(length) {
    if (length === 0) return 0;
    // it s from empirical data, bench.py
    const time = 3.85 - (0.0645 * length) + (0.000284 * Math.pow(length, 2));
    return Math.max(1, Math.round(time)); 
}

sequenceInput.addEventListener('input', () => {
    const sequence = cleanSequence(sequenceInput.value);
    const length = sequence.length;
    
    const estimatedSeconds = calculateEstimatedTime(length);
    
    if (length > 0) {
        seqLengthDisplay.innerHTML = `Longueur: <strong>${length} aa</strong> <span style="color:#666; margin-left:8px;">(⏳ ~${estimatedSeconds}s)</span>`;
    } else {
        seqLengthDisplay.textContent = 'Longueur: 0 aa';
    }
    
    const isValid = validateSequence(sequence);
    
    if (length === 0) {
        seqValidDisplay.textContent = '';
        seqValidDisplay.className = 'badge';
        foldBtn.disabled = true;
    } else if (isValid && length >= 10 && length <= 600) { // Note : j'ai mis à jour la limite 600 ici aussi !
        seqValidDisplay.textContent = '✓ Valide';
        seqValidDisplay.className = 'badge valid';
        foldBtn.disabled = false;
    } else {
        // ... (Gestion des erreurs) ...
        if (length > 600) {
            seqValidDisplay.textContent = '⚠ Trop long (max: 600 aa)';
        } else {
            seqValidDisplay.textContent = '✗ Invalide';
        }
        seqValidDisplay.className = 'badge invalid';
        foldBtn.disabled = true;
    }
});

foldBtn.addEventListener('click', async () => {
    const sequence = cleanSequence(sequenceInput.value);
    const estimated = calculateEstimatedTime(sequence.length);
    
    foldBtn.disabled = true;
    foldBtn.textContent = `Lancement (env. ${estimated}s)...`;
    viewerSection.classList.remove('show'); 
    statusCard.classList.add('show');       
    
    try {
        const response = await apiClient.foldProtein(sequence);
        currentJobId = response.job_id;
        
        jobIdDisplay.textContent = currentJobId;
        statusBadge.textContent  = 'En cours';
        statusBadge.className    = 'badge processing';
        
        await apiClient.pollStatus(currentJobId, updateProgress);
        
        await loadResults(currentJobId);
        
    } catch (error) {
        console.error(error);
        statusBadge.textContent = 'Échec';
        statusBadge.className   = 'badge invalid';
        foldBtn.disabled        = false;
        foldBtn.textContent     = 'Lancer le repliement';
        alert("Erreur: " + error.message);
    }
});

function updateProgress(status) {
    const current = status.progress || 0;
    const total = status.total_steps || 0;
    
    if (total === 0) {
        progressFill.style.width = '5%';
        progressText.textContent = 'Initialisation...';
        return;
    }

    const percent = Math.min(100, (current / total) * 100);
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `Étape ${current}/${total}`;
}

async function loadResults(jobId) {
    try {
        const results = await apiClient.getResults(jobId);
        jobResults = results;
        
        statusBadge.textContent  = '✓ Terminé';
        statusBadge.className    = 'badge completed';
        progressFill.style.width = '100%'; 
        progressText.textContent = `Terminé (${results.steps.length}/${results.steps.length} étapes)`;
        
        if (!viewer) {
            viewer = $3Dmol.createViewer(document.getElementById('mol-viewer'), {
                backgroundColor: 'white'
            });
        }
        
        viewerSection.classList.add('show');
        
        stepSlider.max = results.steps.length - 1;
        stepSlider.value = results.steps.length - 1;
        loadStep(results.steps.length - 1);
        
        foldBtn.disabled = false;
        foldBtn.textContent = ' Lancer le repliement';
        
        viewerSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error("Erreur chargement résultats", error);
        progressText.textContent = "Erreur lors de l'affichage des résultats";
        foldBtn.disabled = false;
        foldBtn.textContent = ' Réessayer';
    }
}

async function loadStep(index) {
    if (!jobResults) return;
    
    const step = jobResults.steps[index];
    stepLabel.textContent = `Etape ${index + 1}/${jobResults.steps.length}`;
    
    try {
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

stepSlider.addEventListener('input', (e) => {
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