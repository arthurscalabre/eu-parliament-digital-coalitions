import pandas as pd
import numpy as np
import os

print("--- ÉTAPE 2 (Méthode experte) : Calcul du taux d'accord brut entre eurodéputés ---")

vote_matrix_path = "outputs/vote_matrix_cleaned.csv"
if not os.path.exists(vote_matrix_path):
    raise FileNotFoundError(f"Le fichier {vote_matrix_path} est introuvable. Relance l'étape 1 !")

vote_matrix = pd.read_csv(vote_matrix_path, index_col="member_id")
print(f"Matrice chargée : {vote_matrix.shape[0]} députés, {vote_matrix.shape[1]} scrutins.")

# 1. Fonction personnalisée pour calculer le taux d'accord proportionnel entre deux vecteurs de vote
def calculate_agreement_matrix(matrix, min_shared_votes=15):
    """
    Calcule le pourcentage de votes identiques entre toutes les paires de députés,
    en ne gardant que les paires ayant au moins min_shared_votes en commun.
    """
    # Conversion en numpy array pour la performance
    values = matrix.values
    index = matrix.index
    n = len(index)
    
    similarity_matrix = np.eye(n) # 1.0 avec soi-même
    
    print(f"Calcul des accords paires à paires (Seuil minimum : {min_shared_votes} votes partagés)...")
    
    for i in range(n):
        for j in range(i + 1, n):
            v1 = values[i]
            v2 = values[j]
            
            # Masque pour ne garder que les scrutins où les deux ont voté (pas de NaN)
            valid = ~np.isnan(v1) & ~np.isnan(v2)
            shared_count = np.sum(valid)
            
            if shared_count >= min_shared_votes:
                # Nombre de fois où les votes sont strictement identiques
                identical = np.sum(v1[valid] == v2[valid])
                agreement_score = identical / shared_count
                similarity_matrix[i, j] = agreement_score
                similarity_matrix[j, i] = agreement_score
            else:
                # Pas assez de votes communs
                similarity_matrix[i, j] = 0.0
                similarity_matrix[j, i] = 0.0
                
        if i % 100 == 0 and i > 0:
            print(f"-> {i} députés traités sur {n}...")

    return pd.DataFrame(similarity_matrix, index=index, columns=index)

# 2. Exécution du calcul avec un seuil strict à 15 votes communs
similarity_df = calculate_agreement_matrix(vote_matrix, min_shared_votes=15)

# 3. Sauvegarde
os.makedirs("outputs", exist_ok=True)
similarity_df.to_parquet("outputs/similarity_matrix.parquet")
print("Matrice d'accord brut sauvegardée dans 'outputs/similarity_matrix.parquet' !")