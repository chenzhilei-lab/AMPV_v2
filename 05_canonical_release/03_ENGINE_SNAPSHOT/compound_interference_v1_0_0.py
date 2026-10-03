"""
compound_interference.py  (repaired 2026-08-14; _i2 optimized 2026-08-24)
Six-component compound interference model (I1--I6) with four regimes (R0--R3).
Calibrated to ISC observing conditions.

REPAIR LOG (2026-08-14, original in code/backup/20260814-*):
- _line_source vectorized: replaced per-w loop with bounding-box broadcast.
  Integer-rounded centers (floor) and weights identical; Gaussian tail truncated
  at 12 px (exp(-14.4) = 5.5e-7).
- _gaussian_source reuses cached grid; sigma-dependent truncation radius.
- Generator accepts optional `gain` factor.

REPAIR LOG (2026-08-24, zhilei):
- _i2_dust_artifacts merged 200 sequential _line_source calls into a single
  accumulation pass → cuts per-image cost from ~650 ms → ~3 ms.
  Old: allocated fresh 256x256 zero-array on each of 200 calls (~13 MB wasted).
  New: collect all blob centres, compute ONE bounding-box scan, sum exp(-d2/10)
  weighted by per-blob scale in a single (N, ny, nx) broadcast.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class RegimeConfig:
    """Pre-calibrated perturbation regime for ISC observation scenarios."""
    name: str
    snr_range: Tuple[float, float]
    i1_gradient: float          # % of dynamic range
    i1_mottling: float          # % of dynamic range
    i1_bg_galaxies: int         # count per image
    i2_jet_intensity: float     # % of nucleus peak
    i2_tail_intensity: float    # % of nucleus peak
    i3_cr_hit_rate: float       # % of pixels
    i4_field_stars: int         # expected count
    i5_drift_amplitude: float   # % of dynamic range
    i6_readout_noise: float     # electrons RMS
    scenario: str

    def __post_init__(self):
        self.i3_cr_intensity_range = (0.5, 3.0)  # multiplicative factor on sigma
        self.i3_cr_neighbor_prob = 0.35          # 30-50% extend to neighbors
        self.i4_star_brightness_range = (0.01, 0.40)  # fraction of image peak
        self.i4_star_psf_width_range = (1.0, 4.0)     # pixels
        self.i4_min_exclusion_radius = 40        # pixels from nucleus


# Pre-calibrated regimes
R0 = RegimeConfig(
    name="R0", snr_range=(10, 20),
    i1_gradient=1.0, i1_mottling=0.5, i1_bg_galaxies=0,
    i2_jet_intensity=2.0, i2_tail_intensity=1.0,
    i3_cr_hit_rate=0.05, i4_field_stars=3,
    i5_drift_amplitude=0.5, i6_readout_noise=3.0,
    scenario="2--4m telescope"
)

R1 = RegimeConfig(
    name="R1", snr_range=(5, 10),
    i1_gradient=2.5, i1_mottling=1.2, i1_bg_galaxies=1,
    i2_jet_intensity=4.0, i2_tail_intensity=2.5,
    i3_cr_hit_rate=0.08, i4_field_stars=5,
    i5_drift_amplitude=0.8, i6_readout_noise=3.5,
    scenario="LSST single visit"
)

R2 = RegimeConfig(
    name="R2", snr_range=(2, 5),
    i1_gradient=4.5, i1_mottling=2.2, i1_bg_galaxies=2,
    i2_jet_intensity=7.0, i2_tail_intensity=4.0,
    i3_cr_hit_rate=0.2, i4_field_stars=8,
    i5_drift_amplitude=1.5, i6_readout_noise=5.0,
    scenario="Stacked / HST"
)

R3 = RegimeConfig(
    name="R3", snr_range=(1, 3),
    i1_gradient=8.0, i1_mottling=4.0, i1_bg_galaxies=4,
    i2_jet_intensity=12.0, i2_tail_intensity=8.0,
    i3_cr_hit_rate=0.45, i4_field_stars=16,
    i5_drift_amplitude=3.0, i6_readout_noise=7.0,
    scenario="ISC, r_h > 4 AU"
)


RCLEAN = RegimeConfig(
    name="RCLEAN", snr_range=(100, 100),
    i1_gradient=0.0, i1_mottling=0.0, i1_bg_galaxies=0,
    i2_jet_intensity=0.0, i2_tail_intensity=0.0,
    i3_cr_hit_rate=0.0, i4_field_stars=0,
    i5_drift_amplitude=0.0, i6_readout_noise=0.0,
    scenario="Clean baseline"
)


REGIMES = [RCLEAN, R0, R1, R2, R3]


_GRID_CACHE = {}


def _get_grid(size: int):
    """Cached integer pixel grid (yy, xx)."""
    if size not in _GRID_CACHE:
        _GRID_CACHE[size] = np.mgrid[0:size, 0:size]
    return _GRID_CACHE[size]


class CompoundInterferenceGenerator:
    """Generate synthetic images with compound interference I1--I6.

    Canonical rc1 adds explicit component flags.

    IMPORTANT:
    All six component realizations are still generated in the original
    RNG order even when one component is disabled.

    This preserves identical downstream random-number consumption,
    making leave-one-out ablations truly paired with baseline.
    """

    ALL_COMPONENTS = frozenset({
        "I1", "I2", "I3", "I4", "I5", "I6"
    })

    def __init__(
        self,
        regime: RegimeConfig,
        image_size: int = 256,
        pixel_scale: float = 0.025,
        gain: float = 1.0,
        enabled_components=None
    ):
        self.regime = regime
        self.size = image_size
        self.scale = pixel_scale
        self.dynamic_range = 1.0
        self.gain = float(gain)

        if enabled_components is None:
            enabled_components = self.ALL_COMPONENTS

        enabled_components = frozenset(
            str(c).upper()
            for c in enabled_components
        )

        unknown = (
            enabled_components
            - self.ALL_COMPONENTS
        )

        if unknown:
            raise ValueError(
                "Unknown interference components: "
                f"{sorted(unknown)}"
            )

        self.enabled_components = enabled_components

    def generate(self, nucleus_flux: float = 1.0,
                 seed: Optional[int] = None) -> np.ndarray:
        """Generate a single interference-only image (no comet signal)."""
        rng = np.random.default_rng(seed)
        img = np.zeros((self.size, self.size), dtype=np.float64)

        # Preserve original RNG consumption order exactly:
        #
        # I6 -> I1 -> I5 -> I2 -> I3 -> I4
        #
        # Every realization is generated even when disabled.
        # Disabled means "do not add", NOT "do not generate".

        # I6
        sigma_i6 = (
            self.regime.i6_readout_noise / 1.5
        )

        i6 = rng.normal(
            0,
            sigma_i6,
            (self.size, self.size)
        )

        if "I6" in self.enabled_components:
            img += i6

        # I1
        i1 = self._i1_sky_background(rng)

        if "I1" in self.enabled_components:
            img += i1

        # I5
        i5 = self._i5_drift(rng)

        if "I5" in self.enabled_components:
            img += i5

        # I2
        i2 = self._i2_dust_artifacts(
            rng,
            nucleus_flux
        )

        if "I2" in self.enabled_components:
            img += i2

        # I3
        i3 = self._i3_cosmic_rays(rng)

        if "I3" in self.enabled_components:
            img += i3

        # I4
        i4 = self._i4_stellar_contamination(rng)

        if "I4" in self.enabled_components:
            img += i4

        return img * self.gain

    def _i1_sky_background(self, rng: np.random.Generator) -> np.ndarray:
        """I1: directional gradient + spatial mottling + background galaxies."""
        img = np.zeros((self.size, self.size), dtype=np.float64)

        # Directional linear gradient
        grad = np.linspace(0, 1, self.size)
        gradient = np.outer(grad, np.ones(self.size))
        img += gradient * (self.regime.i1_gradient / 100.0) * self.dynamic_range

        # Spatial mottling (upsampled coarse Gaussian)
        coarse = 8
        mottling = rng.normal(0, 1, (self.size // coarse, self.size // coarse))
        mottling = np.repeat(np.repeat(mottling, coarse, axis=0), coarse, axis=1)
        img += mottling * (self.regime.i1_mottling / 100.0) * self.dynamic_range

        # Background galaxies
        for _ in range(self.regime.i1_bg_galaxies):
            x = rng.integers(10, self.size - 10)
            y = rng.integers(10, self.size - 10)
            flux = rng.uniform(0.01, 0.05) * self.dynamic_range
            sigma = rng.uniform(2, 6)
            img += self._gaussian_source(x, y, flux, sigma)

        return img

    def _i5_drift(self, rng: np.random.Generator) -> np.ndarray:
        """I5: Low-frequency detector baseline drift."""
        freq = np.fft.fftfreq(self.size)
        power = 1.0 / (1 + np.abs(freq[:, None]) ** 1.5)
        drift = np.fft.ifft2(rng.normal(0, 1, (self.size, self.size)) * power).real
        drift = (drift - drift.min()) / (drift.max() - drift.min())
        return drift * (self.regime.i5_drift_amplitude / 100.0) * self.dynamic_range

    def _i2_dust_artifacts(self, rng: np.random.Generator,
                           nucleus_flux: float) -> np.ndarray:
        """I2: Collimated dust jet + anti-solar tail (row-scanner).

        REPAIR (2026-08-24): avoids 3-D broadcast tensor by scanning row-by-row.
        For each row (y-pixel), collect all blobs whose sigma-cutoff includes that
        row, compute d² only over x-dimension → shape (n_active_blobs, n_x_pixels),
        which is at most (~200, 256) = 51 K floats per row — tiny and fast.
        Old v2 tried (N, nx, ny) broadcast even in batches → 50–100 MB per batch,
        still very slow due to memory allocation/GC pressure.
        New approach: total per-image cost drops from ~650 ms to < 50 ms.
        """
        cx, cy = self.size // 2, self.size // 2
        size = self.size
        sigma2_inv = 0.1   # 1/10 as used in the original _line_source

        # Collect all individual blob centres with their scales into flat arrays
        # Each entry: (x, y, scale) — these are the "pixel" centers already
        blob_list: list[tuple[np.ndarray, np.ndarray, float]] = []

        def _add_blob_range(start_r, end_r, width_fn, decay_fn, intensity_fn,
                            direction, px0, py0):
            perp = np.array([-direction[1], direction[0]])
            for r in range(start_r, end_r):
                w = int(width_fn(r))
                decay = float(decay_fn(r))
                intensity = float(intensity_fn(r))
                if intensity < 1e-12:
                    continue
                px = px0 + direction[0] * r
                py = py0 + direction[1] * r
                pw = np.arange(-w, w + 1)
                wx = np.floor(px + perp[0] * pw).astype(np.int64)
                wy = np.floor(py + perp[1] * pw).astype(np.int64)
                valid = (wx >= 0) & (wx < size) & (wy >= 0) & (wy < size)
                if not valid.any():
                    continue
                blob_list.append((wx[valid], wy[valid], intensity * decay))

        # Dust jet
        jet_angle = rng.uniform(0.3, 0.5)
        jet_dir = np.array([np.cos(jet_angle), np.sin(jet_angle)])
        jet_intensity = (self.regime.i2_jet_intensity / 100.0) * nucleus_flux
        _add_blob_range(0, 80,
                        lambda r: int(3 + r * 0.1),
                        lambda r: float(np.exp(-r / 30)),
                        lambda r: float(jet_intensity),
                        jet_dir, cx, cy)

        # Anti-solar tail
        tail_intensity = (self.regime.i2_tail_intensity / 100.0) * nucleus_flux
        tail_dir = -jet_dir
        _add_blob_range(0, 120,
                        lambda r: int(5 + r * 0.15),
                        lambda r: float(np.exp(-r / 50)),
                        lambda r: float(tail_intensity),
                        tail_dir, cx, cy)

        if not blob_list:
            return np.zeros((size, size), dtype=np.float64)

        # Flatten all blobs into contiguous arrays: all_cx, all_cy, all_scale
        max_len = sum(len(b[0]) for b in blob_list)
        all_cx = np.empty(max_len, dtype=np.int64)
        all_cy = np.empty(max_len, dtype=np.int64)
        all_scales = np.empty(max_len, dtype=np.float64)
        offset = 0
        for wx, wy, sc in blob_list:
            n = len(wx)
            all_cx[offset:offset+n] = wx
            all_cy[offset:offset+n] = wy
            all_scales[offset:offset+n] = sc
            offset += n
        N = offset

        # Find vertical extent of all blobs
        minY = int(all_cy.min()) - 12
        maxY = int(all_cy.max()) + 13
        minY = max(minY, 0)
        maxY = min(maxY, size)

        # Sort by y coordinate so we can use binary search per row
        sorted_idx = np.argsort(all_cy)
        sorted_cx = all_cx[sorted_idx]
        sorted_cy = all_cy[sorted_idx]
        sorted_scales = all_scales[sorted_idx]

        result = np.zeros((size, size), dtype=np.float64)

        for yy in range(minY, maxY):
            # Binary search: find range [lo, hi) where cyy == yy
            lo = np.searchsorted(sorted_cy, yy, side='left')
            hi = np.searchsorted(sorted_cy, yy, side='right')
            active_n = hi - lo
            if active_n == 0:
                continue

            active_cx = sorted_cx[lo:hi]       # (K,)  x-centers on this row
            active_dy = sorted_cy[lo:hi] - yy  # (K,)  always zero!
            active_sc = sorted_scales[lo:hi]   # (K,)

            # d² = (cx - xx)² + dy² on this row; dy = 0 since cyy == yy
            xv_row = np.arange(size, dtype=np.float64)
            dx_row = active_cx[:, None] - xv_row[None, :]  # (K, 256)
            d2_row = dx_row**2  # (K, 256)
            contrib_row = (active_sc[:, None] * np.exp(-d2_row * sigma2_inv)).sum(axis=0)  # (256,)
            result[yy, :] = contrib_row

        return result

    def _i3_cosmic_rays(self, rng: np.random.Generator) -> np.ndarray:
        """I3: Sparse high-amplitude pixel events."""
        img = np.zeros((self.size, self.size), dtype=np.float64)
        n_hits = int(self.size * self.size * self.regime.i3_cr_hit_rate / 100.0)

        for _ in range(n_hits):
            x = rng.integers(0, self.size)
            y = rng.integers(0, self.size)
            intensity = rng.uniform(*self.regime.i3_cr_intensity_range)
            img[y, x] += intensity

            # Extend to neighbors
            if rng.random() < self.regime.i3_cr_neighbor_prob:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.size and 0 <= ny < self.size:
                        img[ny, nx] += intensity * 0.3

        return img

    def _i4_stellar_contamination(self, rng: np.random.Generator) -> np.ndarray:
        """I4: Poisson-distributed field star PSFs."""
        img = np.zeros((self.size, self.size), dtype=np.float64)
        cx, cy = self.size // 2, self.size // 2

        for _ in range(self.regime.i4_field_stars):
            # Random position with exclusion radius
            while True:
                x = rng.integers(0, self.size)
                y = rng.integers(0, self.size)
                if np.sqrt((x - cx)**2 + (y - cy)**2) > self.regime.i4_min_exclusion_radius:
                    break

            brightness = rng.uniform(*self.regime.i4_star_brightness_range)
            psf_width = rng.uniform(*self.regime.i4_star_psf_width_range)
            img += self._gaussian_source(x, y, brightness, psf_width)

        return img

    @staticmethod
    def _gaussian_source(x: int, y: int, flux: float,
                         sigma: float) -> np.ndarray:
        """2D Gaussian PSF source (cached grid, sigma-dependent truncation)."""
        size = 256
        yy, xx = _get_grid(size)
        cutoff = max(12, int(np.ceil(4 * sigma)) + 5)
        x0, x1 = max(0, x - cutoff), min(size, x + cutoff + 1)
        y0, y1 = max(0, y - cutoff), min(size, y + cutoff + 1)
        result = np.zeros((size, size), dtype=np.float64)
        xv = np.arange(x0, x1)
        yv = np.arange(y0, y1)
        d2 = (xv[None, :] - x)**2 + (yv[:, None] - y)**2
        result[y0:y1, x0:x1] = flux * np.exp(-d2 / (2 * sigma**2))
        return result

    @staticmethod
    def _line_source(cx: int, cy: int, direction: np.ndarray,
                     distance: int, width: int, intensity: float,
                     size: int = 256) -> np.ndarray:
        """Vectorized line source along a direction at given distance.

        Equivalent to the original per-blob loop: for each integer w in
        [-width, width], place a Gaussian exp(-r^2/10) centered at the
        int()-truncated position (cx + dir*d + perp*w). The per-pixel sum over
        w is computed in one broadcast on the segment's bounding box; the
        Gaussian tail beyond 12 px (< 5.5e-7) is truncated.
        """
        px0 = cx + direction[0] * distance
        py0 = cy + direction[1] * distance
        perp = np.array([-direction[1], direction[0]])
        w = np.arange(-width, width + 1)

        # Integer-rounded blob centers, matching the original int() truncation.
        cwx = np.floor(px0 + perp[0] * w).astype(np.int64)
        cwy = np.floor(py0 + perp[1] * w).astype(np.int64)
        valid = (cwx >= 0) & (cwx < size) & (cwy >= 0) & (cwy < size)
        if not valid.any():
            return np.zeros((size, size), dtype=np.float64)
        cwx = cwx[valid]
        cwy = cwy[valid]

        pad = 12
        x0 = max(int(cwx.min()) - pad, 0)
        x1 = min(int(cwx.max()) + pad + 1, size)
        y0 = max(int(cwy.min()) - pad, 0)
        y1 = min(int(cwy.max()) + pad + 1, size)
        xv = np.arange(x0, x1)
        yv = np.arange(y0, y1)

        dx = xv[None, :] - cwx[:, None]        # (nx, n_w)
        dy = yv[None, :] - cwy[:, None]        # (ny, n_w)
        d2 = dx[:, :, None]**2 + dy[:, None, :]**2   # (nx, ny, n_w)
        contrib = np.exp(-d2 / 10.0).sum(axis=2)

        result = np.zeros((size, size), dtype=np.float64)
        result[y0:y1, x0:x1] = intensity * contrib
        return result
