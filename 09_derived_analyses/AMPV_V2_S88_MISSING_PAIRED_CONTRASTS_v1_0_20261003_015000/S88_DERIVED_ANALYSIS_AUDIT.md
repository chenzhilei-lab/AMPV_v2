# S88 Missing Paired Contrasts Audit v1.0

Status: PASS

## Source and invariants
Source: authoritative canonical PRODUCTION_ROWS.csv.
SHA-256: ee596bf8028ef454a879a42a7d5d2f7c84bb385c8dc0f7534686f5fe1cd43a94.
Rows: 22,500.
Base sample identities: 300.
Bootstrap replicates: 2,000.
Root analysis seed: 20261002.
No canonical production rerun or mutation.

## Analysis C — paired contamination contrasts
Definition: median paired difference in absolute error at fixed (kappa_ref_target, workflow_id, sample_id), reported as C_high - C=0.
Contrasts: C=.6-C=0 and C=1-C=0.
Total: 50.
95% bootstrap CI strictly positive: 35.
95% CI includes zero: 13.
95% CI strictly negative: 2.

Interpretation:
A positive difference means larger absolute error under contamination. The dominant pattern is degradation with contamination, but it is not universal across all workflow/contrast cells. The two strictly negative intervals occur for privileged-information Workflow D at kappa_ref=20, for both C=.6-C=0 and C=1-C=0. Several Workflow C and D contrasts include zero. Therefore a manuscript-wide statement that contamination monotonically worsens every workflow at every tested contrast is unsupported.

## Analysis D — paired adjacent-kappa contrasts
Definition: median paired difference in absolute error at fixed (C, workflow_id, sample_id), reported as error(kappa_high)-error(kappa_low).
Adjacent pairs: 1->2, 2->5, 5->10, 10->20.
Total: 60.
95% bootstrap CI strictly negative: 60/60.
Includes zero: 0.
Positive: 0.

Interpretation:
Across every tested contamination level, workflow, and adjacent kappa step, higher reference contrast is associated with a lower paired absolute error. This is a strong tested-grid result. It remains descriptive of the frozen COMET_LIKE_PRIMARY/F0 experiment and must not be generalized beyond the tested grid.

## Reconciliation with current manuscript
The S86 manuscript's broad framing is compatible with these results because it emphasizes condition dependence and tested-grid boundaries rather than asserting universal monotonic contamination degradation.
S88 strengthens support for a monotonic tested-grid reference-contrast improvement statement.
Any sentence implying contamination always worsens absolute error in every workflow/cell should be removed or narrowed if found during S89 integration.

## Gate
The two S80 planned but previously unexecuted paired-analysis families are now complete.
This closes the specific S87 scientific-analysis completion gap.
Recommended next stage: S89 integrate the S88 results conservatively into Results/Discussion, audit every affected statement, recompile, then assess FINAL_SCIENTIFIC_FREEZE.
