import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

print("--- ÉTAPE 4 : Heatmaps d'alignement entre groupes politiques ---")

# =============================================================================
# 1. CHARGEMENT
# =============================================================================
for p in ("outputs/similarity_all.parquet", "outputs/similarity_main.parquet",
          "outputs/member_groups.csv", "outputs/digital_votes_list.csv"):
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} introuvable. Relance les étapes 1 et 2 !")


def load_similarity(path):
    sim = pd.read_parquet(path)
    sim.index = sim.index.astype(int)
    sim.columns = sim.columns.astype(int)
    return sim


similarities = {
    "all": load_similarity("outputs/similarity_all.parquet"),
    "main": load_similarity("outputs/similarity_main.parquet"),
}

member_to_group = pd.read_csv("outputs/member_groups.csv", index_col="member_id")["group_code"]
print("Répartition des groupes :\n", member_to_group.value_counts().to_string())

vote_list = pd.read_csv("outputs/digital_votes_list.csv")
n_votes = {
    "all": len(vote_list),
    "main": int((vote_list["is_main"].astype(str).str.lower() == "true").sum()),
}

# Ordre gauche -> droite ; les codes non listés sont ajoutés à la fin
political_order = ["GUE_NGL", "GREEN_EFA", "SD", "RENEW", "EPP", "ECR", "ID", "NI"]
# English labels for political groups
group_labels = { "GUE_NGL": "The Left", "GREEN_EFA": "Greens/EFA", "SD": "S&D", "RENEW": "Renew Europe", "EPP": "EPP", "ECR": "ECR", "ID": "Identity & Democracy", "NI": "Non-attached" }
present = set(member_to_group.unique())
groups = [g for g in political_order if g in present]
groups += sorted(present - set(groups))


# =============================================================================
# 2. MATRICE D'ACCORD MOYEN ENTRE GROUPES
# =============================================================================
def safe_mean_pct(values):
    """Moyenne en % en ignorant les NaN (paires sous le seuil) ; NaN si rien."""
    values = values[~np.isnan(values)]
    return values.mean() * 100 if values.size else np.nan


def compute_group_matrix(sim):
    members = sim.index.intersection(member_to_group.index)
    sim = sim.loc[members, members]
    grp = member_to_group.loc[members]

    # Députés ayant au moins une paire valide (hors diagonale) : effectif réel
    has_pair = (sim.notna().sum(axis=1) - 1) > 0

    gm = pd.DataFrame(index=groups, columns=groups, dtype=float)
    for g1 in groups:
        m1 = grp[grp == g1].index
        for g2 in groups:
            m2 = grp[grp == g2].index
            sub = sim.loc[m1, m2].to_numpy(dtype=float)
            if g1 == g2:
                sub = sub[~np.eye(sub.shape[0], dtype=bool)]   # exclut l'auto-accord (=1)
            gm.loc[g1, g2] = safe_mean_pct(sub.ravel())

    n_eff = {g: int(has_pair[grp[grp == g].index].sum()) for g in groups}
    return gm, n_eff


results = {name: compute_group_matrix(sim) for name, sim in similarities.items()}

for name, (gm, n_eff) in results.items():
    print(f"\nMatrice d'accord moyen (%) - {name} :")
    print(gm.round(1).to_string())

# Échelle de couleurs commune aux deux figures, pour pouvoir les comparer
global_min = min(np.nanmin(gm.to_numpy()) for gm, _ in results.values())
VMIN = float(np.floor(global_min / 5) * 5)
VMAX = 100.0


# =============================================================================
# 3. HEATMAPS
# =============================================================================
sns.set_theme(style="white", font_scale=1.0)
os.makedirs("outputs", exist_ok=True)

titles = {
    "all": "All roll-call votes (including amendments)",
    "main": "Main votes only",
}


def plot_heatmap(name, gm, n_eff):

    # Replace technical group codes with readable English labels
    labels = [
        f"{group_labels.get(g, g)}\n(n={n_eff[g]})"
        for g in gm.index
    ]

    # Larger figure to prevent label overlap
    fig, ax = plt.subplots(figsize=(13, 10), dpi=300)

    sns.heatmap(
        gm,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        vmin=VMIN,
        vmax=VMAX,
        cbar_kws={"label": "Average agreement (%)"},
        linewidths=1.5,
        linecolor="white",
        square=True,
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        annot_kws={"size": 9}
    )

    ax.set_title(
        "Voting alignment between political groups – "
        "DSA, DMA, AI Act, Data Act and CRA "
        "(9th parliamentary term)\n"
        f"{titles[name]}: {n_votes[name]} votes",
        fontsize=13,
        fontweight="bold",
        pad=22
    )

    # Improve axis label readability
    ax.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
        fontsize=8,
        fontweight="bold"
    )

    ax.set_yticklabels(
        labels,
        rotation=0,
        fontsize=9,
        fontweight="bold"
    )

    ax.set_xlabel("Political groups", fontsize=10, labelpad=12)
    ax.set_ylabel("Political groups", fontsize=10, labelpad=12)

    # Explain the number of members displayed in the labels
    fig.text(
        0.5, 0.015,
        "n = members with at least one valid pairwise comparison",
        ha="center",
        fontsize=8,
        color="dimgray"
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    plt.savefig(
        f"outputs/coalitions_heatmap_{name}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Keep CSV group codes unchanged for reproducibility
    gm.round(2).to_csv(
        f"outputs/group_agreement_{name}.csv"
    )

    print(
        f"-> outputs/coalitions_heatmap_{name}.png "
        f"and group_agreement_{name}.csv"
    )


for name, (gm, n_eff) in results.items():
    plot_heatmap(name, gm, n_eff)
