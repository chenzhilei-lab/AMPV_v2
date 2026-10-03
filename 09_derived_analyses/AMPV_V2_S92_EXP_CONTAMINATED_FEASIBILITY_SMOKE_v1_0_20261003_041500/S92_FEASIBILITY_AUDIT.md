# S92-EXP Contaminated Feasibility Smoke v1.0

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
