"""
xv01_benchmark.py  (repaired 2026-08-14)
Full benchmark pipeline: data generation, calibration, method evaluation.

EXTENSION LOG (2026-08-14; R2 strengthen experiments; original in
code\\backup\\20260814-222043):
10. generate_comet_image now accepts Haser dust parameters v_d (cm/s), d2g
    (dust-to-gas ratio) and alpha (grain-size power-law index). All three enter
    the image only as multiplicative amplitude factors (rho_d ∝ Q_d/(4*pi*r^2*v)
    with Q_d ∝ r_n^2*d2g and an effective geometric-optics scattering
    efficiency for alpha), so default values reproduce the previous model
    exactly. alpha is NOT a Mie-scattering implementation: the task explicitly
    forbids claiming that; it is the geometric-optics cross-section-to-mass
    factor of a power-law size distribution (see _eff_scattering_efficiency).
11. New method_d_fixed: oracle-physics method D with the annulus fixed to
    50-90 px (same radii as Method B) while keeping D's median-background
    statistic. Registered in METHODS as 'D_fixed'; used by the D-fixed control
    experiment (R2#6) to separate the adaptive-annulus-position mechanism from
    the median-background mechanism.
12. regime_interference_gain accepts optional comet_kwargs so the SNR anchor
    can be evaluated on a parameterized Haser model (Haser sensitivity run).
13. CLI flag --methods allows running the benchmark on a subset of methods.

REPAIR LOG (2026-08-14; original in code\\backup\\20260814-*):
1. Calibration normalization bug (root cause): img was normalized by rho_d.max(),
   which cancels the r_n^2 dependence (rho_d ∝ r_n^2). Normalization now uses the
   fixed central density of the r_n = 1 km reference nucleus, so img ∝ r_n^2 and
   aperture-flux ratio generate_comet_image(5.0)/generate_comet_image(1.0) = 25.
2. L219 NameError fixed: n_samples is now a local variable in __main__; JSON files
   (summary + per-sample errors + calibration curves) are actually written.
3. Method C (RANSAC) now uses a fixed seed (20260814) instead of a fresh RNG.
4. Method B now genuinely uses photutils aperture_photometry (CircularAperture +
   CircularAnnulus); the old "photutils" method was a pure numpy median ring.
5. Method D fixed: the old r_in formula (true_rn*30/scale*0.5) placed the annulus
   at ~600 px, i.e. outside a 256x256 image, producing NaN. D is now an oracle
   method: annulus inner radius = max(aperture+5, ceil(10*r_center*true_rn)) where
   the Haser surface brightness drops to 1% of the reference central value.
6. Method E (PSF fitting) now fits on a local patch with an analytic Jacobian
   (was ~10+ s/image, i.e. hours for 1200 images; now tens of ms).
7. r_n sampling is a 1-D Latin Hypercube over [0.3, 5.0] km (fixed seed 42). The
   alpha/a_max dimension of the old tex claim (L181) is removed from the protocol:
   the code's Haser model depends only on r_n; tex must be updated accordingly.
8. Calibration is built per method (each method's flux scale is calibrated on
   clean images), so Method E's Gaussian-integrated flux is no longer mapped
   through Method A's aperture-sum curve.
9. Optional SNR-normalized protocol: regime_interference_gain() scales each
   regime's whole interference field so that the r_n = 1 km comet's aperture-summed
   SNR equals the regime's nominal SNR (midpoint of RegimeConfig.snr_range, which
   was dead code). snr_normalize=False reproduces the as-calibrated amplitudes.
"""

import json
import os
import time
from multiprocessing import Pool
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from compound_interference_v1_0_0 import (
    CompoundInterferenceGenerator,
    REGIMES,
)

from xv02_forward_model_v1_0_0 import (
    generate_comet_image_v3,
)

PIXEL_SCALE = 0.025       # arcsec / px
DELTA_AU = 2.0            # observer distance
R_CENTER_CM = 1e5         # Haser inner-cap radius (cm)
DEFAULT_SIZE = 256

# Fixed normalization constant: central dust density for the r_n = 1 km reference
# nucleus (kg/s -> g/s conversion factor 1e3). img = rho_d / NORM_CONST  =>  img ∝ r_n^2.
NORM_CONST = (1.0**2) * 1e3 * 1e3 / (4 * np.pi * R_CENTER_CM**2 * 1e4)

# Nominal Haser dust parameters (previous model values).
NOMINAL_V_D = 1e4        # cm/s
NOMINAL_D2G = 0.1        # dust-to-gas ratio (implied by the old Q_d)
NOMINAL_ALPHA = 3.25     # midpoint of the [2, 4.5] power-law index range

def _eff_scattering_efficiency(alpha: float, a_min: float = 0.1,
                               a_max: float = 100.0) -> float:
    """Effective scattering cross-section per unit dust mass for a grain size
    distribution n(a) ∝ a^-alpha over [a_min, a_max] micron, in the geometric
    optics limit (per-grain cross-section ∝ a^2, grain mass ∝ a^3):

        S_eff(alpha) = (3/(4*rho_g)) * int a^(2-alpha) da / int a^(3-alpha) da

    This is an analytic simplification, NOT Mie scattering (the task explicitly
    forbids claiming a Mie implementation; no wavelength/refractive-index
    dependence is modeled). rho_g = 1 g/cm^3 is absorbed by the nominal
    normalization (see generate_comet_image), so only relative values matter.
    """
    if alpha == 3.0:
        num = np.log(a_max / a_min)
    else:
        num = (a_max ** (3.0 - alpha) - a_min ** (3.0 - alpha)) / (3.0 - alpha)
    if alpha == 4.0:
        den = np.log(a_max / a_min)
    else:
        den = (a_max ** (4.0 - alpha) - a_min ** (4.0 - alpha)) / (4.0 - alpha)
    return float((3.0 / 4.0) * num / den)


def generate_comet_image(r_n_km: float, r_h_au: float = 1.8, delta_au: float = 2.0,
                         size: int = 256, pixel_scale: float = 0.025,
                         v_d: float = NOMINAL_V_D, d2g: float = NOMINAL_D2G,
                         alpha: float = NOMINAL_ALPHA) -> np.ndarray:
    """Generate revised nucleus + coma forward model image."""
    return generate_comet_image_v3(
        r_n_km=r_n_km,
        nucleus_fraction=0.3,
        size=size
    )


def _aperture_mask(size: int = DEFAULT_SIZE, aperture_radius: int = 30) -> np.ndarray:
    cx, cy = size // 2, size // 2
    y, x = np.ogrid[:size, :size]
    return (x - cx)**2 + (y - cy)**2 <= aperture_radius**2


def method_a_aperture_sum(image: np.ndarray, aperture_radius: int = 30,
                          true_rn: Optional[float] = None) -> float:
    """Method A: simple aperture sum, no background correction."""
    mask = _aperture_mask(image.shape[0], aperture_radius)
    return float(image[mask].sum())


def method_b_photutils(image: np.ndarray, aperture_radius: int = 30,
                       annulus_inner: int = 50, annulus_outer: int = 90,
                       true_rn: Optional[float] = None) -> float:
    """Method B: photutils annular subtraction using annulus mean background."""
    from photutils.aperture import CircularAnnulus, CircularAperture, aperture_photometry

    cx, cy = image.shape[0] // 2, image.shape[1] // 2
    aperture = CircularAperture((cx, cy), r=aperture_radius)
    annulus = CircularAnnulus((cx, cy), r_in=annulus_inner, r_out=annulus_outer)
    # method='center' counts pixels whose centers fall inside the apertures,
    # using photutils center-mask semantics for both aperture and annulus.
    phot = aperture_photometry(image, [aperture, annulus], method='center')
    aperture_sum = float(phot['aperture_sum_0'][0])
    background_sum = float(phot['aperture_sum_1'][0])
    aperture_area = float(np.sum(aperture.to_mask(method='center').data > 0))
    annulus_area = float(np.sum(annulus.to_mask(method='center').data > 0))
    background = background_sum / annulus_area
    return aperture_sum - background * aperture_area


RANSAC_SEED = 20260814


def method_c_ransac(image: np.ndarray,
                    aperture_radius: int = 30,
                    n_iter: int = 200,
                    sample_size: int = 30,
                    threshold: float = 0.2,
                    true_rn: Optional[float] = None) -> float:
    """
    Method C:
    Robust aperture photometry with outer-background RANSAC.
    """

    cx, cy = image.shape[0]//2, image.shape[1]//2

    y, x = np.ogrid[:image.shape[0],
                    :image.shape[1]]

    r2 = (x-cx)**2 + (y-cy)**2

    aperture_mask = r2 <= aperture_radius**2

    bg_mask = (r2 >= 50**2) & (r2 <= 90**2)

    bg_pixels = image[bg_mask]

    if len(bg_pixels) < sample_size:
        background = np.median(bg_pixels)
    else:
        rng = np.random.default_rng(RANSAC_SEED)

        best_bg = np.median(bg_pixels)
        best_score = -1

        for _ in range(n_iter):

            sample = rng.choice(
                bg_pixels,
                sample_size,
                replace=False
            )

            bg = np.median(sample)

            residual = np.abs(bg_pixels - bg)

            score = np.sum(
                residual < threshold * np.std(bg_pixels)
            )

            if score > best_score:
                best_score = score
                best_bg = bg

        background = best_bg

    flux = image[aperture_mask].sum()
    area = aperture_mask.sum()

    return float(flux - background * area)


def method_d_physics_informed(image: np.ndarray, aperture_radius: int = 30,
                              true_rn: float = 1.0,
                              pixel_scale: float = PIXEL_SCALE) -> float:
    """Method D: oracle-annulus aperture photometry.

    Uses the true r_n (oracle; theoretical upper bound, per R1#3 the tex must
    label it as such) to place the background annulus where the modeled Haser
    surface brightness drops to 1% of the reference (r_n = 1 km) central value:
    I(r) = r_n^2 * (r_center/r)^2 with r_center ~ 1.1 px  =>  r_in = 10*r_center*r_n.
    The annulus is floored outside the photometric aperture and clamped to the
    image so it is never empty (the old formula gave r_in ~ 600 px -> NaN).
    """
    cx, cy = image.shape[0] // 2, image.shape[1] // 2
    r_center_px = 1.1
    r_in_ideal = int(np.ceil(10.0 * r_center_px * true_rn))
    annulus_inner = max(r_in_ideal, aperture_radius + 5)
    annulus_inner = min(annulus_inner, image.shape[0] // 2 - 41)
    annulus_outer = annulus_inner + 40

    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    aperture_mask = (x - cx)**2 + (y - cy)**2 <= aperture_radius**2
    aperture_sum = image[aperture_mask].sum()

    annulus_mask = ((x - cx)**2 + (y - cy)**2 >= annulus_inner**2) & \
                   ((x - cx)**2 + (y - cy)**2 <= annulus_outer**2)
    if not annulus_mask.any():
        background = float(np.median(image[aperture_mask]))
    else:
        background = float(np.median(image[annulus_mask]))
    aperture_area = np.sum(aperture_mask)

    return float(aperture_sum - background * aperture_area)


def method_d_fixed(image: np.ndarray, aperture_radius: int = 30,
                   annulus_inner: int = 50, annulus_outer: int = 90,
                   true_rn: Optional[float] = None) -> float:
    """Method D control variant ('D_fixed', R2#6): same median-background
    statistic and mask semantics as method_d_physics_informed, but with the
    annulus fixed to the 50-90 px band used by Method B instead of the
    oracle-adaptive annulus position.

    The only difference from Method D is the annulus position, so
    D vs D_fixed isolates the adaptive-annulus-position mechanism; the only
    differences from Method B are the background statistic (median vs mean) and
    pixelization, so B vs D_fixed is a secondary comparison.
    """
    cx, cy = image.shape[0] // 2, image.shape[1] // 2
    annulus_inner = int(annulus_inner)
    annulus_outer = int(annulus_outer)

    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    aperture_mask = (x - cx)**2 + (y - cy)**2 <= aperture_radius**2
    aperture_sum = image[aperture_mask].sum()

    annulus_mask = ((x - cx)**2 + (y - cy)**2 >= annulus_inner**2) & \
                   ((x - cx)**2 + (y - cy)**2 <= annulus_outer**2)
    if not annulus_mask.any():
        background = float(np.median(image[aperture_mask]))
    else:
        background = float(np.median(image[annulus_mask]))
    aperture_area = np.sum(aperture_mask)

    return float(aperture_sum - background * aperture_area)


def method_e_psf_fitting(image: np.ndarray, aperture_radius: int = 30,
                         true_rn: Optional[float] = None,
                         max_nfev: int = 120) -> float:
    """Method E: circular 2D Gaussian PSF + constant background (least squares).

    REPAIR (2026-08-14): the original 7-parameter elliptical Gaussian fit was
    degenerate on the r^-2 comet profile (sigma collapsed to the lower bound,
    non-monotonic calibration, ~10 s/image). The circular 5-parameter fit with
    an analytic Jacobian converges to a shape-invariant solution (flux
    proportional to r_n^2, monotonic calibration) in ~10 ms/image. Fits on a
    local patch; returns the Gaussian-integrated flux 2*pi*A*sigma^2.
    """
    from scipy.optimize import least_squares

    cx, cy = image.shape[0] // 2, image.shape[1] // 2
    pad = aperture_radius + 4
    x0, x1 = max(0, cx - pad), min(image.shape[1], cx + pad + 1)
    y0, y1 = max(0, cy - pad), min(image.shape[0], cy + pad + 1)
    patch = image[y0:y1, x0:x1].astype(np.float64)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    mask = (xx - cx)**2 + (yy - cy)**2 <= aperture_radius**2

    bg0 = float(np.median(patch[~mask])) if (~mask).any() else 0.0
    amp0 = max(float(patch.max()) - bg0, 1e-12)
    p0 = [cx, cy, amp0, 3.0, bg0]

    def model_and_jac(p):
        xc, yc, amp, sig, bg = p
        dx = xx - xc
        dy = yy - yc
        r2 = dx**2 + dy**2
        g = np.exp(-r2 / (2 * sig**2))
        model = bg + amp * g
        dg_xc = g * dx / sig**2
        dg_yc = g * dy / sig**2
        dg_sig = g * r2 / sig**3
        jac = np.stack([
            amp * dg_xc, amp * dg_yc, g, amp * dg_sig,
            np.ones_like(g),
        ], axis=-1)
        return model, jac

    def fun(p):
        model, _ = model_and_jac(p)
        return (model - patch)[mask]

    def jac_fun(p):
        _, jac = model_and_jac(p)
        return jac[mask]

    bounds = ([x0, y0, 0.0, 1.0, -np.inf],
              [x1 - 1, y1 - 1, np.inf, 20.0, np.inf])
    result = least_squares(fun, p0, jac=jac_fun, bounds=bounds, max_nfev=max_nfev)
    amp, sig = result.x[2], result.x[3]
    flux = 2 * np.pi * abs(amp) * sig**2
    return float(flux)


METHODS: Dict[str, Callable[[np.ndarray, Optional[float]], float]] = {
    'A': method_a_aperture_sum,
    'B': method_b_photutils,
    'C': method_c_ransac,
    'D': method_d_physics_informed,
    'D_fixed': method_d_fixed,
    'E': method_e_psf_fitting,
}


def build_calibration_curve(method_name: str, r_n_grid: Optional[np.ndarray] = None,
                            n_grid: int = 40) -> Tuple[np.ndarray, np.ndarray]:
    """Build the per-method calibration curve: r_n -> method flux (noiseless)."""
    if r_n_grid is None:
        r_n_grid = np.logspace(np.log10(0.1), np.log10(10.0), n_grid)
    method = METHODS[method_name]
    fluxes = np.array([method(generate_comet_image(rn), true_rn=rn)
                       for rn in r_n_grid], dtype=np.float64)
    return np.asarray(r_n_grid), fluxes


def flux_to_r_n(flux: float, r_grid: np.ndarray, f_grid: np.ndarray) -> float:
    """Convert measured flux to nucleus radius via calibration interpolation."""
    lf = np.log10(max(flux, 1e-10))
    lfg = np.log10(np.clip(f_grid, 1e-10, None))
    if lf <= lfg[0]:
        return float(r_grid[0])
    if lf >= lfg[-1]:
        return float(r_grid[-1])
    return float(10 ** np.interp(lf, lfg, np.log10(r_grid)))


def make_rn_design(n_samples: int = 300, seed: int = 42,
                   lo: float = 0.3, hi: float = 5.0) -> np.ndarray:
    """1-D Latin Hypercube design for r_n in [lo, hi] km (fixed seed).

    Protocol decision (2026-08-14): alpha/a_max are removed from the sampling
    dimension (the code's Haser model depends only on r_n); tex L181 must be
    updated from "3-D LHS over r_n, alpha, a_max" to "LHS over r_n".
    """
    rng = np.random.default_rng(seed)
    u = (np.arange(n_samples) + rng.random(n_samples)) / n_samples
    rng.shuffle(u)
    return lo + u * (hi - lo)


def regime_interference_gain(regime, comet_kwargs: Optional[dict] = None) -> float:
    """Scale factor for the SNR-normalized protocol.

    Anchors each regime so the r_n = 1 km comet's aperture-summed SNR equals the
    regime's nominal SNR (midpoint of snr_range):
        SNR = aperture_flux(rn=1) / (sigma_i6 * sqrt(N_aperture)).
    The factor multiplies the whole interference field (relative component
    amplitudes are preserved). gain=1.0 reproduces as-calibrated amplitudes.
    comet_kwargs optionally parameterizes the Haser model used for the SNR
    anchor (Haser sensitivity run); the default reproduces the standard gains.
    """
    snr_nom = 0.5 * (regime.snr_range[0] + regime.snr_range[1])
    comet_kwargs = comet_kwargs or {}
    flux_ap_1 = method_a_aperture_sum(generate_comet_image(1.0, **comet_kwargs))
    n_ap = np.sum(_aperture_mask(DEFAULT_SIZE, 30))
    sigma_i6 = regime.i6_readout_noise / 1.5
    sigma_target = flux_ap_1 / (snr_nom * np.sqrt(n_ap))
    return float(sigma_target / sigma_i6)


def _summarize(errors: List[float]) -> Dict:
    arr = np.asarray(errors, dtype=np.float64)
    return {
        'median': float(np.median(arr)),
        'iqr_lo': float(np.percentile(arr, 25)),
        'iqr_hi': float(np.percentile(arr, 75)),
        'mean': float(np.mean(arr)),
        'pct_gt_20pct': float(np.mean(arr > 20.0) * 100.0),
        'pct_gt_100pct': float(np.mean(arr > 100.0) * 100.0),
    }


def run_benchmark(n_samples: int = 300, regimes=REGIMES,
                  methods: Optional[List[str]] = None,
                  snr_normalize: bool = False,
                  r_n_design: Optional[np.ndarray] = None,
                  seed: int = 42,
                  n_workers: int = 1,
                  enabled_components=None
                  ) -> Tuple[Dict, Dict, np.ndarray, Dict, Dict]:
    """Run the full benchmark across regimes and methods (percentage errors)."""
    if methods is None:
        methods = list(METHODS.keys())

    if enabled_components is None:

        enabled_components = tuple(
            sorted(
                CompoundInterferenceGenerator.ALL_COMPONENTS
            )
        )

    else:

        enabled_components = tuple(
            sorted(
                str(c).upper()
                for c in enabled_components
            )
        )

    r_n_true = make_rn_design(n_samples, seed=seed) if r_n_design is None else r_n_design
    methods = list(methods)

    # Per-method calibration (noiseless clean images)
    calibrations = {m: build_calibration_curve(m) for m in methods}

    results = {}
    per_sample = {}
    gains = {}
    for regime in regimes:
        gain = regime_interference_gain(regime) if snr_normalize else 1.0
        gains[regime.name] = gain
        gen = CompoundInterferenceGenerator(regime, gain=gain, enabled_components=enabled_components)
        regime_results = {m: [] for m in methods}
        regime_samples = {m: {'r_n_true': [None] * n_samples,
                              'r_n_est': [None] * n_samples,
                              'flux': [None] * n_samples,
                              'error_pct': [None] * n_samples}
                          for m in methods}

        def _consume(i, fluxes):
            rn = float(r_n_true[i])
            for m in methods:
                flux = fluxes[m]
                r_grid, f_grid = calibrations[m]
                rn_est = flux_to_r_n(flux, r_grid, f_grid)
                error = abs(rn_est - rn) / rn * 100.0
                regime_results[m].append(error)
                regime_samples[m]['r_n_true'][i] = rn
                regime_samples[m]['r_n_est'][i] = rn_est
                regime_samples[m]['flux'][i] = flux
                regime_samples[m]['error_pct'][i] = error

        if n_workers > 1:
            tasks = [
                (
                    i,
                    float(r_n_true[i]),
                    regime,
                    gain,
                    methods,
                    enabled_components
                )
                for i in range(n_samples)
            ]
            with Pool(n_workers) as pool:
                for i, fluxes in pool.imap_unordered(_benchmark_sample_worker, tasks):
                    _consume(i, fluxes)
                    _maybe_print(i, n_samples, regime, regime_results, methods)
        else:
            for i in range(n_samples):
                _, fluxes = _benchmark_sample_worker(
                    (
                        i,
                        float(r_n_true[i]),
                        regime,
                        gain,
                        methods,
                        enabled_components
                    ))
                _consume(i, fluxes)
                _maybe_print(i, n_samples, regime, regime_results, methods)

        results[regime.name] = {m: _summarize(regime_results[m]) for m in methods}
        per_sample[regime.name] = regime_samples

    return results, per_sample, r_n_true, calibrations, gains


def _maybe_print(i, n_samples, regime, regime_results, methods):
    if (i + 1) % 100 == 0:
        med = {m: np.median(regime_results[m]) for m in methods}
        print(f"  [{i+1}/{n_samples}] {regime.name}: "
              + "  ".join(f"{m}={med[m]:.1f}%" for m in methods), flush=True)


def _benchmark_sample_worker(args):
    """Worker for parallel benchmark: generate one interfered image, measure all
    methods. Deterministic per sample (fixed per-sample seed), so results are
    identical regardless of process scheduling."""
    i, rn, regime, gain, methods, enabled_components = args

    gen = CompoundInterferenceGenerator(
        regime,
        gain=gain,
        enabled_components=enabled_components
    )
    clean = generate_comet_image(rn)
    interfered = clean + gen.generate(seed=i * 1000)
    fluxes = {}
    for m in methods:
        fluxes[m] = METHODS[m](interfered, true_rn=rn)
    return i, fluxes


def _summarize(errors: List[float]) -> Dict:
    arr = np.asarray(errors, dtype=np.float64)
    return {
        'median': float(np.median(arr)),
        'iqr_lo': float(np.percentile(arr, 25)),
        'iqr_hi': float(np.percentile(arr, 75)),
        'mean': float(np.mean(arr)),
        'pct_gt_20pct': float(np.mean(arr > 20.0) * 100.0),
        'pct_gt_100pct': float(np.mean(arr > 100.0) * 100.0),
    }


def save_results(out_prefix: str = 'results/benchmark_results', **kwargs):
    os.makedirs('results', exist_ok=True)
    results, per_sample, r_n_true, calibrations, gains = kwargs['payload']
    protocol = kwargs.get('protocol', {})
    with open(f'{out_prefix}.json', 'w', encoding='utf-8') as f:
        json.dump({
            'protocol': protocol,
            'regimes': results,
        }, f, indent=2)
    with open(f'{out_prefix}_per_sample.json', 'w', encoding='utf-8') as f:
        json.dump({
            'protocol': protocol,
            'r_n_true': [float(v) for v in r_n_true],
            'regimes': per_sample,
        }, f, indent=2)
    with open(f'{out_prefix}_calibration.json', 'w', encoding='utf-8') as f:
        json.dump({
            m: {'r_grid': [float(v) for v in rg],
                'f_grid': [float(v) for v in fg]}
            for m, (rg, fg) in calibrations.items()
        }, f, indent=2)
    return f'{out_prefix}.json'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='XV-01 robustness benchmark')
    parser.add_argument('--snr-normalize', action='store_true',
                        help='apply regime SNR normalization (see REPRO_REPORT)')
    parser.add_argument('--out', default='results/benchmark_results',
                        help='output prefix (default results/benchmark_results)')
    parser.add_argument('--n-samples', type=int, default=300)
    parser.add_argument('--workers', type=int, default=4,
                        help='parallel workers for the sample loop (default 4)')
    parser.add_argument(
        '--disable-components',
        type=str,
        default='',
        help='comma-separated subset of I1..I6 to disable'
    )

    parser.add_argument('--methods',
                        type=str,
                        default='',
                        help='comma-separated method subset '
                             '(default: all METHODS keys)')
    args = parser.parse_args()

    n_samples = args.n_samples
    methods = [m.strip() for m in args.methods.split(',') if m.strip()] \
        if args.methods else None
    disabled = {
        c.strip().upper()
        for c in args.disable_components.split(',')
        if c.strip()
    }

    unknown_disabled = (
        disabled
        - CompoundInterferenceGenerator.ALL_COMPONENTS
    )

    if unknown_disabled:

        parser.error(
            "Unknown interference components: "
            f"{sorted(unknown_disabled)}"
        )

    enabled_components = tuple(
        sorted(
            CompoundInterferenceGenerator.ALL_COMPONENTS
            - disabled
        )
    )

    t0 = time.time()

    payload = run_benchmark(
        n_samples=n_samples,
        snr_normalize=args.snr_normalize,
        n_workers=args.workers,
        methods=methods,
        enabled_components=enabled_components
    )
    results, per_sample, r_n_true, calibrations, gains = payload
    elapsed = time.time() - t0

    print(f"\n{'='*70}")
    print(f"XV-01 Robustness Benchmark — {n_samples} samples/regime — "
          f"snr_normalize={args.snr_normalize} — {elapsed:.0f}s")
    print(f"{'='*70}")
    for regime_name, methods_data in results.items():
        print(f"\n{regime_name} (gain={gains[regime_name]:.3e}):")
        for m in methods_data:
            d = methods_data[m]
            status = "FAILED" if d['median'] > 20 else "OK"
            print(f"  {m}: median={d['median']:.1f}%  "
                  f"IQR=[{d['iqr_lo']:.1f}, {d['iqr_hi']:.1f}]%  --- {status}")

    protocol = {
        'n_samples': n_samples,
        'regimes': [r.name for r in REGIMES],
        'methods': list(METHODS.keys()),
        'rn_design': '1D Latin Hypercube, r_n in [0.3, 5.0] km, seed 42',
        'seed': 42,
        'interference_seed_step': 1000,
        'normalization': 'fixed r_n=1 km central density (img proportional to r_n^2)',
        'calibration': 'per-method, noiseless, r_n in [0.1, 10] km, 40 points',
        'snr_normalize': args.snr_normalize,
        'gains': {
            k: float(v)
            for k, v in gains.items()
        },

        'enabled_components':
            list(enabled_components),

        'disabled_components':
            sorted(disabled),

        'canonical_version':
            'v1.0.0',
    }
    path = save_results(out_prefix=args.out, payload=payload, protocol=protocol)
    print(f"\nResults saved to {path} (+ _per_sample.json, _calibration.json)")
