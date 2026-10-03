# AE02A Protocol correction before outcome

Status: PRE-OUTCOME CORRECTION
Date: 2026-10-03

No external-transfer outcome has been generated.

Code-level inspection of the frozen AMPV engine revealed that Photutils is already used by AMPV Method B (CircularAperture, CircularAnnulus, aperture_photometry). Therefore the proposed Photutils experiment in AE02 would not constitute an implementation transfer outside the existing AMPV workflow set and would not adequately answer the reviewer concern.

AE02 is retained as provenance but its choice of external implementation is superseded before any outcome generation.

A genuinely separate implementation is required. SEP was evaluated as the next candidate because it provides a separate source-extraction/photometry implementation, but it is not currently installed. An installation attempt did not produce an importable SEP package, so no SEP scientific run has been performed.

The scientific design constraints frozen in AE02 remain unchanged unless a later pre-outcome protocol amendment explicitly justifies a necessary implementation-specific change:
N=100; kappa={1,5,20}; C={0,0.6,1.0}; tau=0.5; B=2000; matched identities; no outcome-dependent exclusion.

No scientific result exists yet for AE02.
