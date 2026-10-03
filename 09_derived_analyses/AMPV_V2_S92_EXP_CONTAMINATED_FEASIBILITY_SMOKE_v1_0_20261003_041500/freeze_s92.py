from pathlib import Path
import json
b=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S92_EXP_CONTAMINATED_FEASIBILITY_SMOKE_v1_0_20261003_041500")
audit="""# S92-EXP Contaminated Feasibility Smoke v1.0

Status: PASS_TO_PRODUCTION_RUNNER_FREEZE

Purpose: engineering feasibility only. Scientific interpretation of smoke outcomes is prohibited.

Smoke design: sample IDs 0-3; all 5 kappa targets; all 3 C levels; workflows A/B/C/E.
Expected and observed rows: 240.
Core runtime: 2.7621 s.

Structural checks all PASS:
- all numeric outputs finite;
- all sample/kappa/C cells present;
- four workflows per cell;
- sigma_psf paired across conditions;
- F_true scales exactly with kappa;
- E optimizer success for every smoke evaluation;
- C=0 excludes I2P by construction;
- representative-cell determinism exact.

Smoke row SHA-256:
2fe219cb31735bd0e785ca4c46d10b704ed07887f1ae9aa7ec6e608eb39208b9

Engineering note:
Importing the S91 candidate module executes its top-level clean audit and writes extra console output. This does not alter S92 rows, but the production implementation must be refactored into a side-effect-free pure module before protocol hash freeze.

No parameter, hypothesis, stress level, threshold, source range, I2P geometry or workflow definition was changed based on smoke scientific outcomes.

Full N=300 production remains unauthorized until the side-effect-free production module/runner is frozen, audited and hashed.
"""
(b/"S92_FEASIBILITY_AUDIT.md").write_text(audit,encoding="utf-8")
p={"stage":"S92-EXP Contaminated Feasibility Smoke","version":"v1.0","status":"PASS_TO_PRODUCTION_RUNNER_FREEZE","rows":240,"runtime_seconds":2.762075901031494,"all_structural_checks_pass":True,"smoke_row_sha256":"2fe219cb31735bd0e785ca4c46d10b704ed07887f1ae9aa7ec6e608eb39208b9","runner_sha256":"2F51E2BA4705A5245C4FE1CDA086B42F73B6717C30F9DF8558ADFF87E81D3334","base_sha256":"5DADD954B2786168BD5F2D68E7E87279A5FD3A1E45A74F7ED072738C0BD3B5C1","import_side_effect_detected":True,"scientific_interpretation_authorized":False,"full_production_authorized":False,"canonical_modified":False,"existing_production_rerun":False,"next_stage":"S93 side-effect-free production runner and protocol hash freeze"}
(b/"S92_PROVENANCE.json").write_text(json.dumps(p,indent=2),encoding="utf-8")
print("S92_FREEZE_PASS")
