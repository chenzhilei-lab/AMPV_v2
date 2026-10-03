from pathlib import Path
import json
b=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S91_EXP_ISOLATED_IMPLEMENTATION_v1_0_20261003_034000")
audit="""# S91-EXP Isolated Implementation Audit v1.0

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
"""
(b/"S91_IMPLEMENTATION_AUDIT.md").write_text(audit,encoding="utf-8")
p={"stage":"S91-EXP Isolated Implementation","version":"v1.0","status":"PASS_TO_FEASIBILITY_SMOKE","scientific_outcomes_generated":False,"task_family":"COMPACT_PSF_PRIMARY","workflows":["A","B","C","E"],"clean_max_abs_rel_error":{"A":6.617710823775269e-13,"B":6.617710823775269e-13,"C":6.617710823775269e-13,"E":1.7178081179736181e-12},"determinism_pass":True,"candidate_sha256":"5DADD954B2786168BD5F2D68E7E87279A5FD3A1E45A74F7ED072738C0BD3B5C1","feasibility_smoke_authorized":True,"full_production_authorized":False,"canonical_modified":False,"existing_production_rerun":False,"next_stage":"S92 small contaminated feasibility smoke then production protocol freeze"}
(b/"S91_PROVENANCE.json").write_text(json.dumps(p,indent=2),encoding="utf-8")
print("S91_FREEZE_PASS")
