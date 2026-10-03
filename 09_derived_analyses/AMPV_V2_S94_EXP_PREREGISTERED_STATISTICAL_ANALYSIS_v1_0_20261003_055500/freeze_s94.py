from pathlib import Path
import json,hashlib
b=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S94_EXP_PREREGISTERED_STATISTICAL_ANALYSIS_v1_0_20261003_055500")
audit="""# S94-EXP Preregistered Statistical Analysis v1.0

Status: PASS

Source production SHA-256:
44feafab2c14a86a51647103800e7e4c988ca15b136e88911df00bfd168dc948

Analysis: 2000 sample-identity bootstrap replicates, seed 20261004.

Primary results:
- 60 cell summaries, N=300 each.
- 40/40 contamination contrasts (C=.6 or 1 minus C=0) have 95% bootstrap intervals strictly above zero.
- 32/48 adjacent-kappa contrasts have intervals strictly below zero; the remaining 16 are all C=0 clean cells at numerical-floor error. Restricting to C>0 gives 32/32 strictly negative adjacent-kappa intervals.
- 90 blind-workflow paired contrasts: 30 strictly positive, 20 strictly negative, 40 include zero.
- In contaminated cells, E has lower paired absolute error than A/B/C throughout the tested grid; A has lower paired error than B/C; B versus C intervals include zero throughout contaminated cells.
- This must NOT be converted into a universal workflow ranking. E is structurally matched to the circular-Gaussian truth family, so its advantage is family-specific evidence.
- tau sensitivity places operational vulnerability mainly at low kappa/high contamination; for kappa>=5 vulnerability is essentially absent even at tau=.25, aside from one 1/300 C-family event at kappa=5,C=1,tau=.25.

Interpretation:
COMPACT_PSF_PRIMARY produces a reproducible reliability landscape with strong contamination and reference-contrast structure, but its workflow-relative behavior and vulnerability boundary differ materially from COMET_LIKE_PRIMARY. This supports task-dependent AMPV landscape characterization rather than a fixed cross-task ranking.

No post-outcome parameter tuning occurred.
Original COMET_LIKE_PRIMARY canonical remains unchanged.
"""
(b/"S94_SCIENTIFIC_AUDIT.md").write_text(audit,encoding="utf-8")
p={"stage":"S94-EXP Preregistered Statistical Analysis","version":"v1.0","status":"PASS","source_sha256":"44feafab2c14a86a51647103800e7e4c988ca15b136e88911df00bfd168dc948","bootstrap_B":2000,"seed":20261004,"contamination_positive_CI":"40/40","adjacent_kappa_negative_CI_all":"32/48","adjacent_kappa_negative_CI_contaminated":"32/32","workflow_pair_positive":30,"workflow_pair_negative":20,"workflow_pair_zero":40,"post_outcome_tuning":False,"canonical_modified":False,"next_stage":"cross-family structural comparison"}
(b/"S94_PROVENANCE.json").write_text(json.dumps(p,indent=2),encoding="utf-8")
print("S94_FREEZE_PASS")
