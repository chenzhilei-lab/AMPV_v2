# S90-EXP Implementation and Analytic Freeze v1.0

Status: PASS_TO_IMPLEMENTATION

No scientific outcome data generated.

## Gate A - Forward model: PASS
Centered circular Gaussian PSF source; sigma_psf in [1.5,4.0] px; truth estimand is integrated F_true.
Record analytic F_true and finite-grid pixel sum; audit discretization before production.

## Gate B - Interference audit: CONDITIONAL PASS
I1 reusable: sky gradient, mottling, background galaxies.
I2 NOT reusable: implementation is explicitly comet dust jet plus anti-solar tail and depends on nucleus_flux.
I3 reusable: sparse cosmic-ray-like events.
I4 reusable: field-star contamination; helper flux parameter is peak amplitude, not integrated F_true.
I5 reusable: low-frequency detector drift.
I6 reusable: Gaussian readout noise.
Frozen correction: replace I2 by I2P, a task-neutral structured asymmetric local contaminant independent of F_true and sigma_psf.

## Gate C - D oracle proposal: REJECTED PRE-OUTCOME
For Gaussian peak-tail criterion 1e-4, r/sigma=sqrt(2 ln 1e4)=4.2919320526.
With sigma<=4 px, r<=17.17 px; the 30-px aperture forces a safe annulus floor >=35 px.
Therefore true sigma would not change annulus placement. A sigma-adaptive D would be a fake oracle distinction.
Primary workflow set for this family is A/B/C/E unless a meaningful privileged diagnostic is specified before pilot.

## Gate D - Recovery principle
F_true and workflow flux estimates share the same target quantity; do not add a post-hoc calibration surface merely to erase deterministic method bias.
Run a clean-domain numerical audit before production. Any unit/implementation mismatch must be resolved before contaminated outcomes.

## Gate E - Seeds
2-D LHS seed: 20261003.
Analysis/bootstrap seed: 20261004.
Interference namespace: AMPV_V2_COMPACT_PSF_PRIMARY_v1_0.

## Gate F - Output schema
Rows must retain family_id, sample_id, kappa_ref_target, C, workflow_id, F_true, sigma_psf, realized contrast, F_est, signed/absolute error, vulnerability, validity and diagnostics.

## Gate G - Production freeze
NOT YET ELIGIBLE.
Remaining pre-pilot freezes: exact I2P geometry/amplitude, intrinsic-amplitude parameterization, executable isolated code, clean-domain recovery audit.

Next: S91 isolated implementation and non-scientific smoke tests only.