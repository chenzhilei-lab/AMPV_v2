# CAPS Canonical Pipeline v1.0.0

Status:
Release candidate for Gate 1 smoke testing.
NOT approved for production yet.

## Frozen candidate decisions

Forward model:
- copied byte-for-byte from
  04_benchmark/xv02_forward_model.py

Nucleus fraction:
- 0.3

Sampling:
- custom 1-D Latin Hypercube
- r_n in [0.3, 5.0] km
- N=300 for future production
- seed=42

Calibration:
- per-method
- clean/noiseless images
- 40 log-spaced points
- r_n in [0.1, 10] km

SNR normalization:
- False

Method A:
- aperture sum
- no background subtraction

Method B:
- photutils aperture photometry
- aperture radius 30 px
- fixed annulus 50-90 px
- annulus MEAN background

Method C:
- deterministic RANSAC background
- annulus 50-90 px
- RANSAC seed 20260814
- 200 iterations
- sample size 30
- threshold = 0.2 * std(background pixels)

Method D:
- oracle adaptive-annulus diagnostic
- true r_n determines annulus position
- median background

D_fixed:
- fixed 50-90 px annulus
- median background
- diagnostic control only

Method E:
- unchanged from stable runner
- circular 2D Gaussian
- constant background
- analytic Jacobian
- least_squares

Interference baseline:
- full I1-I6 source from
  compound_interference_backup_full_before_ablation.py

Ablation:
- one immutable source file
- explicit enabled_components flags
- no source-code mutation
- disabled components are still generated
  but not added to the image
- RNG consumption therefore remains paired

Promotion rule:
v1.0.0 becomes v1.0.0 only after
the smoke test passes and hashes are recorded.


## Release status
- Gate 1 final audit: PASS
- Promoted from: v1.0.0-rc1
- Production N=300 has NOT yet been run at promotion time.
- This release freezes the protocol/code, not the numerical manuscript results.
