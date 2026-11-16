import os
import numpy as np
import pandas as pd

print("--- ÉTAPE 1 : Téléchargement et filtrage des votes (9e législature) ---")

# =============================================================================
# PARAMÈTRES
# =============================================================================
BASE = "https://github.com/HowTheyVote/data/releases/latest/download/"

# Période : 9e législature (1re session le 2 juillet 2019, dernière avant le 16 juillet 2024)
START_DATE = pd.Timestamp("2019-07-02", tz="UTC")
END_DATE = pd.Timestamp("2024-07-15", tz="UTC")

# Procédures législatives ciblées (code -> nom du texte)
TARGET_PROCEDURES = {
    "2020/0361": "DSA",
    "2020/0374": "DMA",
    "2021/0106": "AI Act",
    "2022/0047": "Data Act",
    "2022/0272": "Cyber Resilience Act",
}

# =============================================================================
# 1. SCRUTINS : filtrage par référence de procédure + période
# =============================================================================
votes_df = pd.read_csv(BASE + "votes.csv.gz", compression="gzip")

needed = ["id", "timestamp", "procedure_reference", "procedure_title", "display_title", "is_main"]
missing = [c for c in needed if c not in votes_df.columns]
assert not missing, f"votes.csv : colonnes manquantes {missing} -> {votes_df.columns.tolist()}"

pattern = "|".join(TARGET_PROCEDURES)
mask = votes_df["procedure_reference"].str.contains(pattern, na=False)
digital_votes = votes_df[mask].copy()

# Nom du texte associé à chaque scrutin (extrait du code de procédure)
code = digital_votes["procedure_reference"].str.extract(f"({pattern})")[0]
digital_votes["text"] = code.map(TARGET_PROCEDURES)

# Filtre de dates explicite
digital_votes["timestamp"] = pd.to_datetime(digital_votes["timestamp"], utc=True)
digital_votes = digital_votes[
    (digital_votes["timestamp"] >= START_DATE) & (digital_votes["timestamp"] <= END_DATE)
]
assert len(digital_votes) > 0, "Aucun scrutin trouvé : vérifier les références de procédure."

# Contrôles : combien de scrutins par texte ? (un texte à 0 = référence à vérifier)
print(f"-> {len(digital_votes)} scrutins retenus, du {digital_votes['timestamp'].min().date()} "
      f"au {digital_votes['timestamp'].max().date()}.")
summary = digital_votes.groupby("text")["is_main"].agg(total="size", principaux="sum")
print(summary.to_string())
for name in TARGET_PROCEDURES.values():
    if name not in summary.index:
        print(f"⚠️  Aucun scrutin trouvé pour : {name}")

os.makedirs("outputs", exist_ok=True)
digital_votes[
    ["id", "timestamp", "text", "procedure_reference", "procedure_title", "display_title", "is_main"]
].sort_values("timestamp").to_csv("outputs/digital_votes_list.csv", index=False)
print("Liste sauvegardée dans 'outputs/digital_votes_list.csv' (à vérifier à la main).")

# =============================================================================
# 2. VOTES INDIVIDUELS
# =============================================================================
print("Téléchargement des votes individuels (fichier volumineux)...")
member_votes_df = pd.read_csv(
    BASE + "member_votes.csv.gz", compression="gzip",
    usecols=["vote_id", "member_id", "position", "group_code"],
)
df = member_votes_df[member_votes_df["vote_id"].isin(digital_votes["id"])].copy()

# Groupe politique principal de chaque député, calculé sur les scrutins du corpus
member_groups = (
    df.dropna(subset=["group_code"])
    .groupby("member_id")["group_code"]
    .agg(lambda x: x.mode().iloc[0])
)
member_groups.to_csv("outputs/member_groups.csv")
print(f"Groupes identifiés pour {len(member_groups)} députés.")

# =============================================================================
# 3. ENCODAGE NUMÉRIQUE
# =============================================================================
print("Valeurs de 'position' rencontrées :", df["position"].unique().tolist())
vote_mapping = {"FOR": 1, "AGAINST": -1, "ABSTENTION": 0, "DID_NOT_VOTE": np.nan}
df["vote_numeric"] = df["position"].map(vote_mapping)

# =============================================================================
# 4. MATRICE DÉPUTÉS x SCRUTINS (aucun seuil de participation :
#    la fiabilité est gérée par paire à l'étape 2)
# =============================================================================
vote_matrix = df.pivot_table(index="member_id", columns="vote_id", values="vote_numeric")

votes_per_mep = vote_matrix.notna().sum(axis=1)
print(f"Matrice : {vote_matrix.shape[0]} députés x {vote_matrix.shape[1]} scrutins.")
print(f"Scrutins exprimés par député : min {votes_per_mep.min()}, "
      f"médiane {int(votes_per_mep.median())}, max {votes_per_mep.max()}.")

vote_matrix.to_csv("outputs/vote_matrix_cleaned.csv")
print("Matrice sauvegardée dans 'outputs/vote_matrix_cleaned.csv'.")