# AE04 SEP external-transfer statistical verdict

Status: PASS — external implementation transfer evidence
Date: 2026-10-03

Input: AE03_PRODUCTION_N100.csv
Input SHA256: 1e098caecdc6f1369688425637f48efcdb3699a5f2648aa430aa66b5b0db2895
Analysis: sample-ID bootstrap, B=2000, seed=20261004, 95% percentile intervals.

## Cell-resolved result
SEP produces a non-degenerate reliability surface outside the AMPV A-E measurement implementation.

Median absolute error:
- kappa=1: C0 ~3.77e-9; C0.6 0.1698 [0.1017,0.1995]; C1 0.2830 [0.1722,0.3325].
- kappa=5: C0 ~3.78e-9; C0.6 0.0340 [0.0207,0.0399]; C1 0.0566 [0.0344,0.0665].
- kappa=20: C0 ~3.78e-9; C0.6 0.00849 [0.00509,0.00998]; C1 0.01415 [0.00861,0.01675].

## Pre-specified stress contrasts
All 6 contamination-vs-clean contrasts have 95% bootstrap intervals strictly above zero.

For reference contrast, the four contaminated-domain comparisons (kappa 1->5 and 5->20 at C=0.6 and C=1.0) have 95% intervals strictly below zero. The two clean-domain comparisons are at numerical floor / unresolved and must not be counted as directional evidence.

Thus the pre-specified transfer-support criterion is satisfied: the independent SEP endpoint yields a cell-resolved reliability surface and systematic bootstrap-supported changes along both pre-specified stress axes in the contaminated domain.

## Operational vulnerability at tau=0.5
Observed vulnerable fraction is nonzero only at kappa=1 in this N=100 transfer case: 0.01 at C=0.6 and 0.10 at C=1.0; all other tested cells are zero. Because the sample is N=100 and the grid is discrete, these values should be reported as tested-cell behavior, not as a continuously estimated boundary.

## Scope
This supports transfer of the AMPV experimental-design logic to an independently implemented SEP photometry endpoint. It does not constitute observational validation, survey validation, or evidence that SEP is generally superior to any AMPV workflow.

## Audit correction
AE04 analysis v1.0 produced correct row-level bootstrap tables but its summary counter for kappa_ci_below_zero used the lower CI bound, yielding 5 instead of 4. v1.1 corrects only that summary index and returns 4. The v1.0 script/summary are retained as provenance.
