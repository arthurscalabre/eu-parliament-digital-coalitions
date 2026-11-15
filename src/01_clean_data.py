import pandas as pd
import numpy as np
import os

print("--- ÉTAPE 1 (Corrigée) : Téléchargement et filtrage des votes du Parlement européen ---")

URL_VOTES = "https://github.com/HowTheyVote/data/releases/latest/download/votes.csv.gz"
URL_MEMBER_VOTES = "https://github.com/HowTheyVote/data/releases/latest/download/member_votes.csv.gz"
URL_MEMBERS = "https://github.com/HowTheyVote/data/releases/latest/download/members.csv.gz"

print("Téléchargement des données en cours...")
votes_df = pd.read_csv(URL_VOTES, compression='gzip')

# Codes de procédures officiels des grands textes numériques de la 9e législature :
# 2020/0361(COD) -> DSA
# 2020/0374(COD) -> DMA
# 2021/0106(COD) -> AI Act
# 2022/0047(COD) -> Data Act
# 2022/0272(COD) -> Cyber Resilience Act
target_procedures = [
    "2020/0361",
    "2020/0374",
    "2021/0106",
    "2022/0047",
    "2022/0272"
]

# Filtrage par la référence de procédure OU par mots-clés dans le titre de la procédure
mask_proc = votes_df['procedure_reference'].str.contains('|'.join(target_procedures), na=False)
mask_title = votes_df['procedure_title'].str.contains('Digital|Artificial Intelligence|Data Act|Cyber', case=False, na=False)

digital_votes = votes_df[mask_proc | mask_title].copy()

print(f"-> {len(digital_votes)} votes identifiés pour les grands textes numériques.")

# Sauvegarde d'un extrait pour vérification
os.makedirs("outputs", exist_ok=True)
digital_votes[["id", "timestamp", "procedure_reference", "procedure_title", "display_title"]].to_csv("outputs/digital_votes_list.csv", index=False)
print("Liste sauvegardée dans 'outputs/digital_votes_list.csv'.")

# Chargement des votes individuels et des membres
member_votes_df = pd.read_csv(URL_MEMBER_VOTES, compression='gzip')
members_df = pd.read_csv(URL_MEMBERS, compression='gzip')

# Fusion avec les votes individuels (attention, la colonne ID dans votes_df s'appelle 'id' et dans member_votes_df 'vote_id')
df = member_votes_df[member_votes_df['vote_id'].isin(digital_votes['id'])].copy()

# Encodage numérique des votes
vote_mapping = {
    "FOR": 1,
    "AGAINST": -1,
    "ABSTENTION": 0,
    "DID_NOT_VOTE": np.nan,
    "REJECTED": np.nan
}
df['vote_numeric'] = df['position'].map(vote_mapping)

# Création de la matrice pivot : Lignes = Députés (member_id), Colonnes = Scrutins (vote_id)
vote_matrix = df.pivot_table(
    index="member_id",
    columns="vote_id",
    values="vote_numeric"
)

# Nettoyage : on garde les députés ayant participé à une part significative des votes
vote_matrix = vote_matrix.dropna(thresh=int(vote_matrix.shape[1] * 0.3), axis=0)

print(f"Matrice finale prête : {vote_matrix.shape[0]} députés et {vote_matrix.shape[1]} scrutins.")
vote_matrix.to_csv("outputs/vote_matrix_cleaned.csv")
print("Matrice sauvegardée dans 'outputs/vote_matrix_cleaned.csv' !")