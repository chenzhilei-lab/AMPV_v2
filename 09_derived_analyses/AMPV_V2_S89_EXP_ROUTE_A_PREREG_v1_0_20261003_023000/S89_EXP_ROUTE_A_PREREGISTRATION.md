# S89-EXP Route A Pre-registration v1.0
## Second synthetic family: COMPACT_PSF_PRIMARY

Status: DESIGN_FROZEN_FOR_IMPLEMENTATION_AUDIT — NO PILOT OR OUTCOME DATA GENERATED

## 1. Scientific purpose

Primary question:
Does the AMPV validation design recover a structured, workflow-dependent reliability landscape when the source family changes materially from an extended comet nucleus+coma profile to compact PSF-like source photometry?

This is a transfer test of the validation methodology, not an attempt to prove universal astronomical generality.

The existing COMET_LIKE_PRIMARY/F0 production remains frozen, authoritative, and untouched.

## 2. Why this family

COMPACT_PSF_PRIMARY changes the measurement morphology from an extended nucleus+coma profile to a compact centrally concentrated source while retaining a photometric task for which aperture/background methods and Gaussian model fitting remain scientifically interpretable.

Rejected for this extension:
- merely changing comet sigma, coma fraction, or image size: insufficiently distinct;
- extended galaxy morphology: current A-E are not uniformly task-appropriate;
- blended binaries/crowded multi-source deblending as the primary family: this changes the estimand from photometry to source separation and would require new workflows;
- real-image injection: reserved as a later external-validity extension.

## 3. Forward model

Image size: 256 x 256 pixels.

Truth source:
a circular Gaussian PSF-like source centered at the image center.

Source profile:
I(x,y) = F_true / (2*pi*sigma_psf^2) * exp[-r^2/(2*sigma_psf^2)].

Primary truth estimand:
F_true, the integrated source flux.

Shape nuisance parameter:
sigma_psf is sampled independently per base sample from a predeclared interval [1.5, 4.0] pixels using a second Latin-hypercube dimension.

This makes the family materially different from COMET_LIKE_PRIMARY while remaining compatible with the existing circular photometric workflows.

No coma component is present.

## 4. Base sample design and independence

N = 300 base sample identities.

Each base identity contains:
- one latent source-flux coordinate used to define a normalized source before reference-contrast gain;
- one sigma_psf value in [1.5,4.0] px;
- one frozen structured-contamination realization/seeds.

Sampling:
2-D Latin hypercube with a new extension-specific fixed seed to be frozen in the implementation stage. The seed must be chosen before any outcome is examined and recorded in source/provenance.

The 300 identities, not condition-specific rendered images, are the statistical units.

## 5. Stress grid

Retain the AMPV two-axis logic:
reference contrast kappa_ref = {1,2,5,10,20}
contamination level C = {0,0.6,1.0}

15 condition cells per base identity.
4,500 condition-specific scenes before workflow expansion.

Reference contrast definition:
for a fixed reference PSF source with sigma_psf = 2.5 px, choose source gain so that the clean source flux measured by the reference 30-pixel aperture divided by I6 sigma*sqrt(N_aperture) equals target kappa_ref.

Important:
configured kappa_ref is an experimental stress coordinate, not a claim that every variable-sigma sample has exactly that realized SNR. Realized sample-specific contrast must be recorded separately.

## 6. Contamination model

Primary design choice:
reuse the frozen I1-I6 compound-interference generator and the same paired structured-realization logic unless implementation audit identifies a component that is semantically tied specifically to comet morphology.

Reason:
holding the contamination generator fixed while changing the source family isolates transfer across source morphology more cleanly than simultaneously changing both source and contamination.

Required pre-run audit:
verify I1-I6 code line-by-line for source-family dependence. If any component uses comet truth or morphology, freeze an explicit adaptation before pilot. No silent adaptation is allowed.

## 7. Workflows

A:
30-pixel aperture sum, no background subtraction.

B:
30-pixel aperture plus fixed 50-90 px annulus mean background.

C:
same aperture/annulus geometry with deterministic RANSAC-style background estimator. Retain the existing algorithmic settings unless an implementation audit proves incompatibility.

E:
blind circular 2-D Gaussian plus constant background. This is naturally matched to the new family, but remains blind to true F and sigma.

D:
must NOT reuse the comet-specific true-r_n annulus formula.

Pre-registered D information class:
ORACLE_DIAGNOSTIC using the true sigma_psf only to choose an adaptive background-annulus inner radius from a fixed predeclared multiple of sigma_psf, floored outside the 30-pixel aperture and clamped by image geometry; median background estimation.

The exact multiplier must be frozen from analytic Gaussian tail containment before any outcome data are generated. It must not be tuned against workflow performance.

D remains excluded from blind-workflow superiority claims.

## 8. Calibration / estimand recovery

Primary estimand is F_true.

Because A-D return aperture/background-corrected flux and E returns Gaussian-integrated flux, each workflow must be calibrated on clean noiseless images across the predeclared source-flux and sigma_psf domain.

Preferred implementation:
use direct flux recovery when analytically valid and verify it against a clean calibration surface. If a calibration surface is required, its grid/interpolation method must be frozen before pilot.

Do not reuse the comet r_n calibration curve.

## 9. Primary outcome

Signed relative flux error:
e_F = (F_est - F_true)/F_true.

Primary continuous outcome:
|e_F|.

Primary reporting remains cell-resolved; no pooled global winner is primary.

## 10. Operational vulnerability

Primary threshold:
|e_F| > 0.5.

Reason:
retain the same operational 50% relative-error criterion as the first family to enable cross-family methodological comparison, while explicitly not treating 0.5 as a universal astronomical standard.

Sensitivity set:
tau = {0.25,0.4,0.5,0.6,0.75,1.0}.

Continuous error remains primary.

## 11. Primary hypotheses / expectations

H1 — reference-contrast structure:
Within each workflow and contamination level, increasing kappa_ref is expected to reduce paired absolute flux error on average. Test with predeclared adjacent-kappa paired contrasts.

H2 — contamination structure:
Increasing C is expected to alter paired absolute error, but no universal monotonic degradation across every workflow/cell is predeclared. Test C=.6-C=0 and C=1-C=0.

H3 — workflow dependence:
Blind workflows A/B/C/E are expected to show non-identical cell-resolved error/vulnerability surfaces. No global best workflow is predeclared.

H4 — task-family transfer:
AMPV is considered methodologically informative if the second family yields interpretable, reproducible cell-resolved reliability structure under the frozen design. Replicating the exact ranking or boundary pattern of COMET_LIKE_PRIMARY is NOT a success criterion.

No hypothesis is stated for D as a blind competitor; D is a privileged-information diagnostic.

## 12. Paired analyses

All paired analyses use matched sample identities.

Required:
- cell-level median absolute and signed error;
- vulnerability rate;
- 95% cluster-bootstrap intervals;
- blind workflow paired contrasts A/B/C/E;
- contamination contrasts C=.6-C=0 and C=1-C=0;
- adjacent-kappa contrasts 1->2, 2->5, 5->10, 10->20;
- tau sensitivity;
- optimizer/failure sensitivity for E if non-success occurs.

Bootstrap:
2,000 replicates.
Resampling unit: base sample identity.
A new extension-specific analysis seed must be frozen before execution.

## 13. Failure handling

Every workflow evaluation must emit a validity/diagnostic record.

Computational exception:
record as computational failure; do not silently impute.

Optimizer non-success without exception:
retain separately in diagnostics and conduct sensitivity analysis rather than automatically rewriting canonical validity, unless the new protocol explicitly defines otherwise before execution.

Out-of-domain calibration:
must be flagged, counted, and handled by a frozen rule; no silent clipping chosen after seeing results.

## 14. Sample size and stopping rule

Production target: N=300 base identities, matching the first family for design comparability.

Pilot:
a small implementation-only smoke test is permitted solely to verify deterministic generation, finite outputs, calibration monotonicity/coverage, workflow execution, row counts, seed pairing, and runtime.

Pilot outcomes must NOT be used to choose stress levels, tau, workflow definitions, sigma range, or hypotheses.

No early stopping based on favorable/unfavorable scientific results.

Full production occurs once after promotion gate PASS.

## 15. Required promotion gates before production

Gate A: forward-model analytic audit.
Gate B: I1-I6 source-family-independence audit.
Gate C: D oracle-annulus analytic rule freeze.
Gate D: calibration/recovery audit across full truth domain.
Gate E: deterministic paired-seed smoke test.
Gate F: workflow output/failure schema audit.
Gate G: production protocol hash freeze.

Only after A-G PASS may N=300 production run.

## 16. Planned reporting

Main comparison:
COMET_LIKE_PRIMARY versus COMPACT_PSF_PRIMARY at the level of reliability-landscape structure, not by forcing identical numerical boundaries.

Report:
- family-specific cell error/vulnerability landscapes;
- whether adjacent-kappa direction is consistent within each family;
- contamination effects and their heterogeneity;
- changes in workflow-relative behavior;
- information-class distinction for D;
- boundary sensitivity to tau.

Do not pool both families into one global score.

## 17. Success/failure interpretation

Scientifically informative outcomes include:
- similar reliability structure across families;
- substantially different workflow behavior across families;
- failure of an expected monotonic kappa trend;
- different contamination sensitivity;
- a workflow that is strong in one family and weak in the other.

None of these outcomes may be discarded because they weaken the current narrative.

## 18. Claim ceiling after this extension

If successfully executed, AMPV may be described as demonstrated on two materially distinct controlled synthetic photometric task families.

It still may NOT be described as observationally validated, universally general, or validated across astronomical pipelines. Those require Route B/C evidence.

## 19. Freeze decision

This document freezes the scientific design concept but does NOT yet authorize production.

Next stage:
implementation audit and analytic freeze for COMPACT_PSF_PRIMARY, especially:
1. I1-I6 family-independence;
2. exact D annulus multiplier;
3. truth-flux sampling parameterization and 2-D LHS seed;
4. calibration/recovery rule;
5. extension-specific analysis seed.
No scientific outcome data should be generated before those decisions are frozen.
