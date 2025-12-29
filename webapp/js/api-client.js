/**
 * Client API pour communiquer avec le backend FastAPI
 * Ce fichier est réutilisable dans Angular (à adapter en TypeScript)
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ProteinFoldingAPI {
    /**
     * Lance un job de repliement protéique
     * @param {string} sequence - Séquence d'acides aminés
     * @param {string|null} jobId - ID personnalisé (optionnel)
     * @returns {Promise<{job_id: string, status: string, message: string}>}
     */
    async foldProtein(sequence, jobId = null) {
        const response = await fetch(`${API_BASE_URL}/fold`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sequence: sequence,
                job_id: jobId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors du lancement du folding');
        }

        return await response.json();
    }

    /**
     * Récupère le statut d'un job
     * @param {string} jobId - ID du job
     * @returns {Promise<{job_id: string, status: string, progress: number, total_steps: number}>}
     */
    async getStatus(jobId) {
        const response = await fetch(`${API_BASE_URL}/status/${jobId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Job introuvable');
        }

        return await response.json();
    }

    /**
     * Récupère les résultats d'un job complété (ou partiels)
     * @param {string} jobId - ID du job
     * @returns {Promise<{job_id: string, sequence: string, status: string, steps: Array}>}
     */
    async getResults(jobId) {
        const response = await fetch(`${API_BASE_URL}/results/${jobId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Résultats introuvables');
        }

        return await response.json();
    }

    /**
     * Supprime les résultats d'un job
     * @param {string} jobId - ID du job
     * @returns {Promise<{message: string}>}
     */
    async deleteResults(jobId) {
        const response = await fetch(`${API_BASE_URL}/results/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la suppression');
        }

        return await response.json();
    }

    /**
     * Récupère le contenu d'un fichier PDB
     * @param {string} pdbUrl - URL relative du fichier PDB
     * @returns {Promise<string>} - Contenu du fichier PDB
     */
    async fetchPDB(pdbUrl) {
        // Si l'URL est relative, on ajoute l'origine si nécessaire, 
        // sinon fetch le gère souvent bien. Ici on s'assure que c'est propre.
        const url = pdbUrl.startsWith('http') ? pdbUrl : `http://localhost:8000${pdbUrl}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement du PDB');
        }

        return await response.text();
    }

    /**
     * Polling du statut jusqu'à complétion
     * @param {string} jobId - ID du job
     * @param {Function} onProgress - Callback appelé à chaque mise à jour avec l'objet status
     * @param {number} interval - Intervalle en ms entre chaque requête (défaut: 2000)
     * @returns {Promise<Object>} - Statut final
     */
    async pollStatus(jobId, onProgress = null, interval = 2000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getStatus(jobId);
                    
                    // C'est ICI que la magie opère : on notifie l'extérieur
                    if (onProgress) {
                        onProgress(status);
                    }

                    if (status.status === 'completed') {
                        resolve(status);
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Le folding a échoué'));
                    } else {
                        // On continue d'attendre
                        setTimeout(poll, interval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }
}

// Export pour utilisation dans d'autres fichiers
const apiClient = new ProteinFoldingAPI();