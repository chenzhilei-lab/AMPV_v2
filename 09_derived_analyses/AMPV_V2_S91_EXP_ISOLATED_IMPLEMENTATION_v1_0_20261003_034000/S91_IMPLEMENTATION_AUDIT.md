# S91-EXP Isolated Implementation Audit v1.0

Status: PASS_TO_FEASIBILITY_SMOKE

No scientific outcome data were generated.

Frozen family: COMPACT_PSF_PRIMARY.
Primary workflows: A/B/C/E.
Truth: integrated Gaussian source flux F_true.
sigma_psf range: 1.5-4.0 px.
Intrinsic amplitude factor: 0.8-1.2.
2-D LHS seed: 20261003.
Analysis seed reserved: 20261004.

I2P freeze:
- asymmetric elliptical local residual;
- center distance 38-70 px from target;
- major sigma 5-12 px;
- minor sigma 1.5-3.5 px;
- random orientation from base seed;
- peak amplitude = 0.02*F_REF*contamination level;
- F_REF=1000;
- no dependence on sample F_true or sigma_psf.

Clean-domain audit:
A/B/C max absolute relative error <= 6.62e-13.
E max absolute relative error <= 1.72e-12.
No calibration surface is required.

Determinism:
source PASS; I2P PASS; 2-D LHS PASS.

Implementation candidate SHA-256:
5DADD954B2786168BD5F2D68E7E87279A5FD3A1E45A74F7ED072738C0BD3B5C1

Gate decision:
A small contaminated feasibility smoke test is now allowed solely to verify finite outputs, stress scaling, paired identity preservation, row schema and runtime. It must not be used to change hypotheses, tau, stress levels, I2P geometry, sigma range, amplitude range, or workflow definitions. Full N=300 production remains unauthorized until the feasibility smoke passes and a dedicated production runner/protocol hash are frozen.
