# AMPV V2

AMPV V2 (Astronomical Measurement Pipeline Validation) is a reproducible validation methodology for stress-testing astronomical photometric workflows under controlled compound contamination.

This repository package contains the code, frozen protocols, canonical numerical outputs, verification assets, figures, and derived analyses used to support the AMPV V2 manuscript.

## Repository structure

- 01_core_engine — frozen AMPV V2 core implementation assets.
- 02_workflows — production workflow runners.
- 03_experiment_protocols — experiment definitions and protocol records.
- 04_pilot — pilot-stage records retained for provenance.
- 05_canonical_release — authoritative canonical release AMPV_V2_CANONICAL_RELEASE_20261002_074007.
- 06_numerical_ledger — frozen numerical ledger.
- 07_verification — verification and reproducibility checks.
- 08_figures — manuscript/result figure assets and figure-generation records.
- 09_derived_analyses — derived analyses, including S88 paired contrasts and the pre-specified S89-S94 compact-PSF extension.

## Canonical evidence

The authoritative comet-like canonical release included here is:
AMPV_V2_CANONICAL_RELEASE_20261002_074007

The compact-PSF extension is retained separately under 09_derived_analyses. It is not part of the original comet-like canonical production.

## Reproducibility and provenance

SHA256SUMS.txt records SHA256 hashes for the repository package. PROVENANCE_MANIFEST.csv provides a file-level inventory.

The repository package is a publication/reproducibility copy. The original project development history and internal audit archive are intentionally not duplicated wholesale here.

## Scope

The study is synthetic and single-fidelity. Repository inclusion does not broaden the scientific claims beyond the tested validation domains described in the manuscript.

## License

No open-source license has been assigned in this package. A license should be selected by the author before public release if reuse permissions are intended.

## Author

Zhilei Chen
Guangdong Peizheng College
ORCID: 0009-0000-2798-9566
Contact: 2604513@peizheng.edu.cn


Additional publication assets:
- 05a_native_production — authoritative native production snapshot underlying the canonical release.
- 10_manuscript_and_supplement — current manuscript source, compiled PDF, figures, and supplementary material.

