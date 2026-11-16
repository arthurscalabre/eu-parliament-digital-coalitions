import math
import os

import numpy as np
import pandas as pd

print("--- ÉTAPE 2 : Taux d'accord entre eurodéputés (tous scrutins + votes principaux) ---")

# =============================================================================
# PARAMÈTRES
# =============================================================================
MIN_SHARED_MAX = 15      # nb de votes communs exigé par paire (plafond)
MIN_SHARED_RATIO = 0.5   # ... mais jamais plus de 50 % des scrutins de la matrice,
                         # sinon le corpus "votes principaux" (peu de scrutins) serait vide

# =============================================================================
# 1. CHARGEMENT
# =============================================================================
matrix_path = "outputs/vote_matrix_cleaned.csv"
list_path = "outputs/digital_votes_list.csv"
for p in (matrix_path, list_path):
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} introuvable. Relance l'étape 1 !")

vote_matrix = pd.read_csv(matrix_path, index_col="member_id")
vote_matrix.columns = vote_matrix.columns.astype(int)   # les en-têtes CSV sont du texte

vote_list = pd.read_csv(list_path)
is_main = vote_list["is_main"].astype(str).str.lower() == "true"
main_ids = set(vote_list.loc[is_main, "id"])
main_cols = [c for c in vote_matrix.columns if c in main_ids]

matrices = {
    "all": vote_matrix,            # tous les scrutins (amendements compris)
    "main": vote_matrix[main_cols] # votes principaux uniquement
}
print(f"Scrutins : {vote_matrix.shape[1]} au total, {len(main_cols)} votes principaux.")
assert len(main_cols) > 0, "Aucun vote principal dans le corpus."


# =============================================================================
# 2. TAUX D'ACCORD PAR PAIRE (vectorisé)
# =============================================================================
def compute_agreement(matrix: pd.DataFrame) -> pd.DataFrame:
    """Part de scrutins identiquement votés, sur les scrutins où les deux ont voté.
    Paires sous le seuil de votes communs -> NaN (inconnu, pas 0)."""
    M = matrix.to_numpy(dtype=float)
    valid = (~np.isnan(M)).astype(float)

    # Nb de scrutins où les deux députés ont voté
    common = valid @ valid.T

    # Nb de scrutins où ils ont voté pareil (pour, contre ou abstention).
    # NaN == v vaut False : les absences ne comptent jamais comme un accord.
    agree = np.zeros_like(common)
    for v in (-1.0, 0.0, 1.0):
        ind = (M == v).astype(float)
        agree += ind @ ind.T

    min_shared = max(1, min(MIN_SHARED_MAX, math.ceil(MIN_SHARED_RATIO * M.shape[1])))
    with np.errstate(divide="ignore", invalid="ignore"):
        score = np.where(common >= min_shared, agree / common, np.nan)
    np.fill_diagonal(score, 1.0)

    n = M.shape[0]
    n_pairs = n * (n - 1) / 2
    n_valid = np.count_nonzero(~np.isnan(np.triu(score, k=1)))
    print(f"   seuil : {min_shared} votes communs | paires valides : "
          f"{n_valid}/{int(n_pairs)} ({100 * n_valid / n_pairs:.1f} %)")
    return pd.DataFrame(score, index=matrix.index, columns=matrix.index)


# =============================================================================
# 3. CALCUL ET SAUVEGARDE
# =============================================================================
os.makedirs("outputs", exist_ok=True)
for name, mat in matrices.items():
    print(f"Calcul : {name} ({mat.shape[0]} députés x {mat.shape[1]} scrutins)")
    sim = compute_agreement(mat)
    out = sim.copy()
    out.columns = out.columns.astype(str)   # Parquet exige des noms de colonnes en texte
    out.to_parquet(f"outputs/similarity_{name}.parquet")
    print(f"   -> outputs/similarity_{name}.parquet")