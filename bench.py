import time
import random
import matplotlib.pyplot as plt
import sys
import os
import torch  # <--- Ajouté
import gc     # <--- Ajouté

# Ajoute le dossier courant au path pour pouvoir importer 'api'
sys.path.append(os.getcwd())

try:
    from api.services.fold_engine import engine
except ImportError:
    print("❌ Erreur : Impossible d'importer 'api'.")
    print("Assurez-vous de lancer ce script depuis la RACINE du projet.")
    sys.exit(1)

def generate_random_sequence(length):
    """Génère une séquence aléatoire d'acides aminés valide."""
    valid_aa = "ACDEFGHIKLMNPQRSTVWY"
    return "".join(random.choice(valid_aa) for _ in range(length))

def run_benchmark():
    # Liste complète des longueurs
    lengths = [10, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 800, 900, 1000, 1200]
    # on bout d'un moment pus assez de vram donc ça swapp, on s'arrete, 16Go -> 600 max
    times = []

    print("Chargement du modèle (peut prendre quelques secondes)...")
    start_load = time.time()
    engine.load()
    print(f"Modèle chargé en {time.time() - start_load:.2f}s")

    print("Warmup (exécution à vide)...")
    engine.predict(generate_random_sequence(20))
    
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    
    print("Démarrage du benchmark !\n")

    print(f"{'Longueur':<10} | {'Temps (s)':<10}")
    print("-" * 25)

    for length in lengths:
        seq = generate_random_sequence(length)
        
        t0 = time.time()
        
        engine.predict(seq)
        
        t1 = time.time()
        duration = t1 - t0
        times.append(duration)
        
        print(f"{length:<10} | {duration:.4f}")

        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    try:
        plt.figure(figsize=(10, 6))
        plt.plot(lengths, times, marker='o', linestyle='-', color='#667eea', linewidth=2)
        plt.title('Performance ESMFold : Temps vs Longueur')
        plt.xlabel('Longueur de la séquence (aa)')
        plt.ylabel('Temps d\'inférence (secondes)')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        output_file = 'benchmark_result.png'
        plt.savefig(output_file)
        print(f"\nGraphique sauvegardé sous : {output_file}")
    except Exception as e:
        print(f"\nImpossible de générer le graphique : {e}")

if __name__ == "__main__":
    run_benchmark()