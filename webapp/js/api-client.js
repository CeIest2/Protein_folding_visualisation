/**
 * Client API simplifié
 */
const API_BASE_URL = '/api'; // URL relative (plus robuste)

const apiClient = {
    // 1. Lancer le job
    async foldProtein(sequence) {
        const res = await fetch(`${API_BASE_URL}/fold`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sequence })
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Erreur lors du lancement');
        }
        return await res.json();
    },

    // 2. Récupérer les résultats
    async getResults(jobId) {
        const res = await fetch(`${API_BASE_URL}/results/${jobId}`);
        if (!res.ok) throw new Error('Résultats introuvables');
        return await res.json();
    },

    // 3. Récupérer le fichier PDB (structure 3D)
    async fetchPDB(url) {
        // Gère les URLs relatives ou absolues automatiquement
        const res = await fetch(url);
        if (!res.ok) throw new Error('Erreur chargement PDB');
        return await res.text();
    },

    // 4. Système de surveillance (Polling)
    async pollStatus(jobId, onProgress, interval = 200) {
        return new Promise((resolve, reject) => {
            const check = async () => {
                try {
                    const res = await fetch(`${API_BASE_URL}/status/${jobId}`);
                    if (!res.ok) throw new Error('Erreur statut');
                    
                    const status = await res.json();
                    
                    // Notifier la progression
                    if (onProgress) onProgress(status);

                    if (status.status === 'completed') {
                        resolve(status); // Fini !
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Échec du folding'));
                    } else {
                        setTimeout(check, interval);
                    }
                } catch (e) { 
                    reject(e); 
                }
            };
            check(); // Premier appel
        });
    }
};