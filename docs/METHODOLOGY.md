# Methodology — Analysis of Voting Behaviour on European Digital Legislation

## 1. Research Objective

This project examines voting behaviour in the European Parliament during its 9th parliamentary term (2019–2024), focusing on five cornerstone legislative files regulating the digital sector.

The goal is twofold:
1. Measure pairwise voting agreement between individual Members of the European Parliament (MEPs) and aggregate these patterns by political group.
2. Assess how coalition dynamics shift when comparing **all recorded votes** (including detailed amendments) against **main votes** (final texts and major legislative milestones).

Rather than inferring ideological proximity or formal coalition agreements directly, this analysis quantifies observed behavioural similarity within a well-defined legislative corpus.

---

## 2. Data Sources and Corpus Construction

### 2.1. Source Datasets
Roll-call voting records are retrieved from [HowTheyVote.eu](https://howtheyvote.eu), which provides structured, machine-readable archives of European Parliament proceedings:
* `votes.csv.gz`: Metadata for each recorded vote, including timestamps, procedure references, and vote classifications.
* `member_votes.csv.gz`: Individual voting positions and political group affiliations for every MEP on each scrutiny.

### 2.2. Selection Criteria
The corpus isolates all recorded votes linked to five major digital regulations adopted during the 9th term (2 July 2019 – 15 July 2024):

| Legislative Text | Procedure Reference |
| :--- | :--- |
| Digital Services Act (DSA) | `2020/0361` |
| Digital Markets Act (DMA) | `2020/0374` |
| Artificial Intelligence Act (AI Act) | `2021/0106` |
| Data Act | `2022/0047` |
| Cyber Resilience Act (CRA) | `2022/0272` |

### 2.3. Analytical Granularity: All Votes vs. Main Votes
Using the `is_main` flag provided in the source dataset, two distinct corpora are constructed:
* **Complete Corpus (`all`):** All 206 recorded votes tied to the five procedures, capturing amendments, split votes, and procedural motions.
* **Main Votes Corpus (`main`):** Only the 9 votes classified as `is_main`[cite: 5], reflecting final adoption and major plenary positions.

---

## 3. Data Preparation

### 3.1. Political Group Attribution
Each MEP is assigned to a single political group based on the `group_code` field in `member_votes.csv.gz`. When an MEP changed affiliation during the term, their most frequently recorded group (the statistical mode) is retained to ensure consistent group-level aggregation.

### 3.2. Numerical Encoding
Individual voting positions are mapped to numerical values as follows:

| Recorded Position | Numerical Value | Interpretation |
| :--- | :---: | :--- |
| `FOR` | `+1` | In favour |
| `AGAINST` | `-1` | Opposed |
| `ABSTENTION` | `0` | Formal abstention |
| `DID_NOT_VOTE` | `NaN` | Absent / non-participating |

Absences (`DID_NOT_VOTE`) are treated as missing observations rather than expressions of disagreement and are excluded from pairwise comparisons.

### 3.3. Individual Voting Matrix
The cleaned data is structured into an $M \times V$ matrix where rows represent individual MEPs, columns represent recorded votes, and cells contain the encoded positions.

---

## 4. Pairwise Voting Agreement

### 4.1. Proportional Agreement Index
Rather than using Pearson correlation—which is sensitive to zero-variance vectors when votes are near-unanimous—similarity is measured via a direct proportional agreement index. For every pair of MEPs $(i, j)$, let:
* $C_{ij}$ be the number of votes in which **both** MEPs expressed a recorded position (`FOR`, `AGAINST`, or `ABSTENTION`).
* $A_{ij}$ be the number of those shared votes in which both MEPs adopted the **exact same position**.

The pairwise agreement score $S_{ij}$ is defined as:

$$S_{ij} = \frac{A_{ij}}{C_{ij}}$$

Scores range from $0$ (complete disagreement across all shared votes) to $1$ (identical voting record across all shared votes).

### 4.2. Minimum Shared-Vote Threshold
To prevent pairs with very few overlapping votes from skewing the distribution, an agreement score is only retained if the two MEPs participated in at least $T$ common votes, where $T$ scales with corpus size $N$:

$$T = \max\left(1, \min\left(15, \lceil 0.5N \rceil\right)\right)$$

If $C_{ij} < T$, the score $S_{ij}$ is set to `NaN` and excluded from subsequent averages. This adaptive rule enforces a strict 15-vote minimum on the complete corpus ($N=206$) while remaining valid on the smaller main-vote subset ($N=9$, where $T=5$).

### 4.3. Similarity Matrices
This calculation produces two symmetric MEP $\times$ MEP similarity matrices (`similarity_all.parquet` and `similarity_main.parquet`), with the main diagonal set to $1$.

---

## 5. Political Group Aggregation

### 5.1. Inter-Group Agreement
To evaluate alignment between two distinct political groups $G_A$ and $G_B$, we compute the arithmetic mean of all valid individual pairwise scores between their respective members. Let $P_{AB}$ be the set of valid MEP pairs $(i, j)$ with $i \in G_A$, $j \in G_B$, and $S_{ij} \neq \text{NaN}$:

$$S_{AB} = \frac{1}{|P_{AB}|} \sum_{(i,j) \in P_{AB}} S_{ij}$$

Each valid pair carries equal weight regardless of the exact number of shared votes above threshold $T$.

### 5.2. Intra-Group Cohesion
Internal group cohesion ($S_{AA}$) is calculated using the same formula across all distinct pairs of MEPs belonging to the same group ($i \neq j$), excluding self-comparisons.

### 5.3. Effective Participation Count
Alongside each group label on the visualisations, the effective sample size ($n$) indicates the number of MEPs within that group who met the minimum shared-vote threshold for at least one valid comparison.

---

## 6. Visualisation and Exports

The resulting group-level matrices are exported as CSV tables (`group_agreement_all.csv`, `group_agreement_main.csv`) and visualised as annotated heatmaps (`coalitions_heatmap_all.png`, `coalitions_heatmap_main.png`). Political groups are ordered along the traditional European Parliament left–right spectrum (`GUE_NGL` to `ID`, followed by `NI`) on a shared colour scale ($30\%$ to $100\%$) to allow direct visual comparison between amendment-level and final-vote dynamics.

---

## 7. Methodological Limitations

1. **Corpus Specificity:** Results reflect voting behaviour across five digital files and should not be generalised to all policy areas (e.g., environmental or agricultural legislation, where coalition patterns often diverge).
2. **Static Group Attribution:** Assigning each MEP to their modal political group smooths over mid-term party switches and individual defections.
3. **Unweighted Pairwise Averaging:** Because group scores average individual pairwise rates equally, a pair sharing 15 votes contributes the same weight as a pair sharing 200 votes.
4. **Behavioural vs. Ideological Alignment:** Identical votes do not automatically imply shared political intent; groups on opposite ends of the spectrum may vote `AGAINST` the same compromise text for entirely different reasons.
5. **Small Sample Size for Main Votes:** With $N=9$, the main-vote heatmap captures high-level consensus on final texts but is sensitive to individual abstentions or absences.

---

## 8. Reproducibility

The pipeline is implemented in Python (`NumPy`, `Pandas`, `Matplotlib`, `Seaborn`, `PyArrow`). All scripts and configuration parameters are version-controlled in `src/` to allow full end-to-end reproduction from raw data download to figure generation.