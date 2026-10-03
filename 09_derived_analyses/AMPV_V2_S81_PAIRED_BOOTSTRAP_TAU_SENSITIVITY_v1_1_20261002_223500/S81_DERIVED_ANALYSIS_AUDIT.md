# S81 Derived-analysis Audit v1.1

Status: PASS

Input: authoritative canonical PRODUCTION_ROWS.csv only.
Rows=22,500; base sample identities=300; cell-workflow groups=75; each group N=300.
Bootstrap: 2,000 replicates, fixed seed 20261002, sample_id as cluster/resampling unit.

## Reconciliation
The tau=0.5 lowest-tested-kappa boundaries exactly reproduce the frozen S66 table:
A 5/5/5; B 5/5/5; C 20/20/20; D 5/5/5; E 1/2/2 for C=0/0.6/1.0.
Therefore the new threshold pipeline reconciles with the frozen primary analysis.

## Tau sensitivity
Boundary locations are threshold-dependent, as expected. At tau=0.4 the pattern is close to tau=0.5 but A at C=1 shifts from K=5 to K=10. At tau=0.6, E at C=0.6 shifts from K=2 to K=1 while A/B/C/D retain the tau=0.5 boundaries. At tau=0.25, workflow C does not reach <=5% vulnerability anywhere in the tested grid. At tau=0.75 and 1.0 many boundaries move to lower K.
Interpretation: tau=0.5 must remain an operational frozen threshold, not a universal physical boundary. Continuous error surfaces remain primary; sensitivity should be reported.

## Paired workflow contrasts
Blind-workflow paired contrasts quantify the cell-resolved separations without treating rows as independent. C-minus-E median absolute-error differences are positive in all 15 cells with 95% cluster-bootstrap intervals above zero. A-minus-E and B-minus-E are also positive in all 15 cells with intervals above zero. A-versus-B is condition-dependent: at C=0 A tends to have slightly lower paired absolute error; at C=0.6/1.0 B tends to have lower paired absolute error, with the low-K C=0 intervals touching zero in some cells.
These are condition-specific effect estimates, not a global ranking claim.

## Workflow E optimizer-status sensitivity
Three E evaluations have optimizer success=False/status=0 but remained valid under the frozen exception-based production validity rule. Excluding those three changes cell median absolute error by at most 9.02434481125005e-05. No material change to the reported reliability landscape is indicated by this sensitivity check.

## Engineering history
S81 v1.0 used a statistically valid but inefficient DataFrame concatenate bootstrap implementation and was terminated for performance before output completion. S81 v1.1 preserved the statistical definition and replaced the implementation with sample-axis NumPy resampling. Scientific impact of v1.0 termination: NONE.

## Decision
Derived uncertainty/paired/tau-sensitivity analysis is numerically coherent with the frozen canonical point estimates and can proceed to manuscript-integration review. Canonical production remains unchanged; no production rerun was performed.
