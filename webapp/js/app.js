/**
 * Application principale - Gestion de l'interface utilisateur
 */

// Éléments du DOM
const sequenceInput = document.getElementById('sequenceInput');
const seqLengthDisplay = document.getElementById('seqLength');
const seqValidDisplay = document.getElementById('seqValid');
const foldBtn = document.getElementById('foldBtn');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const jobIdDisplay = document.getElementById('jobIdDisplay');
const statusBadge = document.getElementById('statusBadge');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsList = document.getElementById('resultsList');

// État de l'application
let currentJobId = null;

// Validation de la séquence en temps réel
sequenceInput.addEventListener('input', () => {
    const sequence = cleanSequence(sequenceInput.value);
    const length = sequence.length;
    
    seqLengthDisplay.textContent = `Longueur: ${length} aa`;
    
    // Validation
    const isValid = validateSequence(sequence);
    
    if (length === 0) {
        seqValidDisplay.textContent = '';
        seqValidDisplay.className = 'status-badge';
        foldBtn.disabled = true;
    } else if (isValid && length >= 10 && length <= 1000) {
        seqValidDisplay.textContent = '✓ Séquence valide';
        seqValidDisplay.className = 'status-badge valid';
        foldBtn.disabled = false;
    } else {
        if (length < 10) {
            seqValidDisplay.textContent = '⚠ Trop court (min: 10 aa)';
        } else if (length > 1000) {
            seqValidDisplay.textContent = '⚠ Trop long (max: 1000 aa)';
        } else {
            seqValidDisplay.textContent = '✗ Caractères invalides';
        }
        seqValidDisplay.className = 'status-badge invalid';
        foldBtn.disabled = true;
    }
});

// Bouton de lancement du folding
foldBtn.addEventListener('click', async () => {
    const sequence = cleanSequence(sequenceInput.value);
    
    if (!validateSequence(sequence)) {
        alert('Séquence invalide !');
        return;
    }
    
    // Désactiver le bouton
    foldBtn.disabled = true;
    foldBtn.innerHTML = '<span class="loading"></span> Lancement...';
    
    try {
        // Lancer le folding
        const response = await apiClient.foldProtein(sequence);
        currentJobId = response.job_id;
        
        // Afficher la section de statut
        statusSection.style.display = 'block';
        jobIdDisplay.textContent = currentJobId;
        statusBadge.textContent = 'En traitement';
        statusBadge.className = 'status-badge processing';
        
        // Scroller vers la section de statut
        statusSection.scrollIntoView({ behavior: 'smooth' });
        
        // Démarrer le polling
        await apiClient.pollStatus(currentJobId, updateProgress);
        
        // Une fois complété, charger les résultats
        await loadResults(currentJobId);
        
    } catch (error) {
        console.error('Erreur:', error);
        alert(`Erreur: ${error.message}`);
        
        statusBadge.textContent = 'Échec';
        statusBadge.className = 'status-badge failed';
    } finally {
        // Réactiver le bouton
        foldBtn.disabled = false;
        foldBtn.innerHTML = '<span class="btn-text">🚀 Lancer le repliement</span>';
    }
});

/**
 * Met à jour l'interface avec la progression
 */
function updateProgress(status) {
    const percent = (status.progress / status.total_steps) * 100;
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `Étape ${status.progress}/${status.total_steps} - Calcul en cours...`;
    
    console.log(`📊 Progression: ${status.progress}/${status.total_steps}`);
}

/**
 * Charge et affiche les résultats
 */
async function loadResults(jobId) {
    try {
        const results = await apiClient.getResults(jobId);
        
        // Mettre à jour le statut
        statusBadge.textContent = '✓ Complété';
        statusBadge.className = 'status-badge completed';
        progressFill.style.width = '100%';
        progressText.textContent = `✅ Folding terminé ! ${results.steps.length} étapes générées.`;
        
        // Afficher la section de résultats
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Afficher la liste des fichiers générés
        displayResults(results);
        
    } catch (error) {
        console.error('Erreur chargement résultats:', error);
        alert(`Erreur lors du chargement des résultats: ${error.message}`);
    }
}

/**
 * Affiche la liste des résultats
 */
function displayResults(results) {
    resultsList.innerHTML = '';
    
    const infoCard = document.createElement('div');
    infoCard.className = 'result-item';
    infoCard.innerHTML = `
        <div>
            <strong>Séquence:</strong> ${results.sequence.substring(0, 50)}... (${results.sequence.length} aa)<br>
            <strong>pLDDT moyen:</strong> ${results.steps[0].avg_plddt.toFixed(2)}
        </div>
    `;
    resultsList.appendChild(infoCard);
    
    // Liste des fichiers PDB
    results.steps.forEach(step => {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.innerHTML = `
            <span>📄 Étape ${step.step + 1}/${results.steps.length}</span>
            <a href="${step.pdb_url}" target="_blank" download>Télécharger PDB</a>
        `;
        resultsList.appendChild(item);
    });
}

/**
 * Nettoie une séquence (enlève espaces, retours à la ligne, etc.)
 */
function cleanSequence(seq) {
    return seq.toUpperCase().replace(/\s+/g, '').replace(/\n/g, '');
}

/**
 * Valide qu'une séquence ne contient que des acides aminés valides
 */
function validateSequence(seq) {
    const validAA = 'ACDEFGHIKLMNPQRSTVWY';
    return seq.split('').every(char => validAA.includes(char));
}

// Message de bienvenue dans la console
console.log('🧬 Protein Folding Visualizer - Ready!');
console.log('API Base URL:', 'http://localhost:8000/api');