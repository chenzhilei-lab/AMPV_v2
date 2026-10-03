# AMPV V2

AMPV V2 (Astronomical Measurement Pipeline Validation) is a reproducible methodology for stress-testing astronomical photometric workflows under controlled compound contamination.

This publication package contains the frozen primary comet-like production, compact-PSF extension, independent SEP implementation-transfer experiment, manuscript candidate, supplementary material, and supporting provenance.

## Repository structure

- 01_core_engine — frozen AMPV V2 core implementation.
- 02_workflows — production workflow runners.
- 03_experiment_protocols — frozen experiment definitions.
- 04_pilot — pilot/provenance records.
- 05a_native_production and 05_canonical_release — authoritative primary comet-like production and canonical release.
- 06_numerical_ledger — frozen numerical ledger.
- 07_verification — verification and reproducibility checks.
- 08_figures — figure assets and generation records.
- 09_derived_analyses — paired analyses, compact-PSF extension, and SEP implementation-transfer evidence.
- 10_manuscript_and_supplement — current acceptance-candidate manuscript and self-contained supplement.

## Evidence boundaries

The original comet-like canonical release is AMPV_V2_CANONICAL_RELEASE_20261002_074007. The compact-PSF extension and SEP transfer experiment are separately versioned derived experiments and do not modify that canonical production.

The SEP transfer uses SEP 1.4.1 on synthetic compact-PSF scenes with known source position. It tests implementation transfer only; it is not observational validation and does not establish a task-independent workflow ranking.

## Reproducibility

The acceptance-package checksum is SHA256SUMS_ACCEPTANCE_v1_2.txt. PROVENANCE_MANIFEST_ACCEPTANCE_v1_2.csv is the refreshed file-level inventory. Historical checksum/manifest files are retained as provenance and should not be interpreted as the current package inventory.

## Scope

The study remains synthetic and single-fidelity. Results and operational boundaries apply only to the tested task families and stress grids.

## License

No open-source license has been assigned. A license should be selected by the author before public release if explicit reuse permissions are intended.

## Author

Zhilei Chen  
Guangdong Peizheng College  
ORCID: 0009-0000-2798-9566  
Contact: 2604513@peizheng.edu.cn
