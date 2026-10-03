# AE03 SEP external-transfer implementation freeze v1.0

Status: PRE-OUTCOME IMPLEMENTATION FROZEN
Date: 2026-10-03

## Runtime
Python 3.12 isolated runtime.
SEP 1.4.1.
NumPy 2.5.3.
No modification to the AMPV Python 3.14 environment.

## Scientific design
This implements the still-active scientific constraints from AE02/AE02A:
N=100 matched identities; kappa={1,5,20}; C={0,0.6,1.0}; tau=0.5; cluster bootstrap B=2000.

## Scene construction
Reuse the S93 compact-PSF task-family construction without changing its source or contamination semantics:
- 256x256 image
- Gaussian source
- F_REF=1000
- amplitude-factor LHS range [0.8,1.2]
- sigma LHS range [1.5,4.0]
- LHS seed 20261003
- neutral-field seed 910000+sample_id
- I2P seed 920000+sample_id
- same identity-specific neutral/I2P realization across all nine stress cells
- F = F_REF * amplitude_factor * kappa
- image = clean + C*(neutral_field + I2P)

Only kappa is reduced from the S93 five-level grid to the pre-frozen transfer subset {1,5,20}; C is unchanged.

## External measurement endpoint
Use SEP 1.4.1 sep.sum_circle at fixed source center (128,128), aperture radius 30 px, with bkgann=(50,90) and subpix=0.

Rationale: SEP documentation states that sum_circle performs circular-aperture summation and can estimate/subtract a local background from a supplied annulus. subpix=0 requests exact overlap. This endpoint is implemented by SEP, not Photutils and not the AMPV A-E measurement functions.

No source detection/recentering is introduced because the transfer question concerns measurement implementation under the same known matched scene, not detection completeness.

## Calibration / truth
For this compact source family, F_true is the total injected Gaussian flux. SEP aperture/background measurement is compared directly with F_true using signed relative error and absolute relative error, matching the S93 family metric definition.

## Output and flags
Record SEP flux, SEP flag, signed_error, absolute_error, vulnerable_tau_0_5 for every identity/cell.
No rows may be silently dropped for SEP flags. Flag counts are reported.

## Smoke gate before production
A separate N=3 smoke run is permitted only for software/shape/finite/flag checking. Smoke outcomes are not scientific evidence and must not be used to alter the frozen scientific design.

Production is authorized only if:
- 27 rows are produced in smoke;
- all numerical outputs are finite;
- sample/cell uniqueness is exact;
- SEP call succeeds for all rows.

## Production interpretation
As frozen in AE02: transfer support does not require SEP to outperform an internal workflow. It requires a non-degenerate cell-resolved reliability surface and bootstrap-supported systematic change across at least one pre-specified stress axis. Null/mixed results remain reportable.
