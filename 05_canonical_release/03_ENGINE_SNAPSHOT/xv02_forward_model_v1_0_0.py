import numpy as np

def generate_nucleus_component(r_n_km: float, size: int = 256, sigma_pix: float = 1.5) -> np.ndarray:
    cx = cy = size // 2
    y, x = np.mgrid[:size, :size]
    psf = np.exp(-((x-cx)**2 + (y-cy)**2)/(2*sigma_pix**2))
    psf /= psf.sum()
    return psf * (r_n_km**2)


def generate_haser_coma(r_n_km: float, size: int = 256) -> np.ndarray:
    cx = cy = size // 2
    y, x = np.mgrid[:size, :size]
    rho = np.sqrt((x-cx)**2 + (y-cy)**2)
    rho = np.maximum(rho, 1.0)
    coma = r_n_km**2 / rho**2
    coma /= coma.max()
    return coma * (r_n_km**2)


def generate_comet_image_v3(r_n_km: float, nucleus_fraction: float = 0.7, size: int = 256) -> np.ndarray:
    nucleus = generate_nucleus_component(r_n_km, size=size)
    coma = generate_haser_coma(r_n_km, size=size)
    return nucleus_fraction * nucleus + (1-nucleus_fraction) * coma
