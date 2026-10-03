# AMPV V2 — S4 Production Grid Design & Freeze v1.0

## Purpose

Freeze the formal AMPV V2 production grid after the S3 pilot and S3X targeted low-kappa extension.

This stage **does not run production** and **does not authorize production**.

## Frozen grid candidate

- `kappa_ref = {1, 2, 5, 10, 20}`
- `C = {0.0, 0.6, 1.0}`
- `N = 300` matched realizations per cell
- workflows `A-E`
- fidelity `F0`
- task family `COMET_LIKE_PRIMARY`

Totals:

- 15 cells
- 4500 matched scenes
- 22500 workflow evaluations

## Why these kappa_ref levels

The original S3 pilot sampled high/safe reference levels (`80, 20, 5`) and showed little vulnerability.
S3X then probed `kappa_ref=2` and `1`, where vulnerability increased materially, especially for Method C.

The production design therefore preserves dense coverage of the transition/stress region:

- 1 and 2: observed low-kappa stress region
- 5: bridge to the original pilot
- 10 and 20: transition/safe-region anchors

`40` and `80` are not retained in the primary production grid because the pilot showed low information gain there for failure-boundary mapping.

## Why these contamination levels

`C={0.0,0.6,1.0}` preserves the original pilot's contamination design and provides:
- no structured contamination,
- intermediate contamination,
- full contamination.

## Pairing

All workflows within a matched scene must share the same underlying realization identity.
The production seed namespace is new (`AMPV_PRODUCTION_v1_0`) so production is cleanly separated from pilot evidence.

## Important interpretation note

`kappa_ref` is the reference control value used by the simulator. Sample-specific realized `Ksample`
varies with the matched `r_n` realization. Production analysis must therefore retain both the
configured `kappa_ref` and realized per-sample kappa.

## Runtime

Using the observed S3 runtime:
- median projection for 4500 matched scenes: ~8.57 min
- p95 projection: ~9.33 min

Server is not recommended at this stage.

## Gate

Production remains unauthorized until:
1. local S4 config audit passes,
2. canonical hashes pass,
3. grid counts pass,
4. seed policy passes,
5. path/output policy passes,
6. S4 freeze is appended to the worklog.
