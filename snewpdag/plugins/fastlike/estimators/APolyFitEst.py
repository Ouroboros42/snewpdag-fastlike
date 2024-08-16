"""
PolyFitLag - estimate burst time from a polynomial fit likelihood of Poisson distributed burst data

Optional:
    poly_degree: degree of polynomial to fit
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt

from .EstimatorBase import EstimatorBase
from .poly_util import valid_real_roots

from itertools import islice

def iter_pairs(iterable):
    pair_ready = False
    for item in iterable:
        if pair_ready:
            yield np.array((last, item))
        else:
            last = item

        pair_ready = not pair_ready

def signed_diff(x: ArrayLike, center: ArrayLike):    
    diff = x - center
    return (diff > 0).astype(int), np.abs(diff)

def apoly(x: ArrayLike, peak_x: float, peak_y: float, *arms_interleaved: float):
    is_pos, diff = signed_diff(x, peak_x)

    return peak_y + sum(c[is_pos] * (diff ** (n + 2)) for n, c in enumerate(iter_pairs(arms_interleaved)))

def apolyderiv(x: ArrayLike, peak_x: float, peak_y: float, *arms_interleaved: float):
    is_pos, diff = signed_diff(x, peak_x)

    return sum((n + 2) * c[is_pos] * (diff ** (n + 1)) for n, c in enumerate(iter_pairs(arms_interleaved)))

def apolyjac(x: float, peak_x: float, peak_y: float, *arms_interleaved: float):
    is_pos, diff = signed_diff(x, peak_x)
    n_coeffs = len(arms_interleaved) // 2

    d_peak_x = np.where(is_pos, -1, 1) * apolyderiv(x, peak_x, peak_y, *arms_interleaved)
    d_peak_y = np.ones_like(x)

    zeros = np.zeros_like(x)
    pows = tuple(diff ** (n + 2) for n in range(n_coeffs))

    d_coeffs = tuple(np.where(is_pos == bool(i%2), pows[i//2], zeros) for i in range(2 * n_coeffs))

    return np.stack((d_peak_x, d_peak_y) + d_coeffs, axis=1)

class APolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, **kwargs):
        self.poly_terms = poly_degree - 1
        super().__init__(**kwargs)

    def apoly_bounds(self, lag_mesh):
        n_extra_terms = 2 * (self.poly_terms - 1)

        # Quadratic terms must be negative at peak
        lower = np.array([ np.min(lag_mesh), -np.inf, -np.inf, -np.inf ] + [ -np.inf ] * n_extra_terms)
        upper = np.array([ np.max(lag_mesh),  np.inf,  0     ,  0      ] + [  np.inf ] * n_extra_terms) 

        return lower, upper

    def apoly_init(self, lag_mesh, like_mesh):
        peak_index = np.argmax(like_mesh)
        max_log_likelihood = like_mesh[peak_index]
        peak_lag = lag_mesh[peak_index]

        return np.array([ peak_lag, max_log_likelihood ] + [0] * (self.poly_terms * 2))

    def find_err(self, arm_coeffs, max_lag_rel):
        domain = (0, max_lag_rel)
        poly = Polynomial((0.5, 0, *arm_coeffs), domain, domain)
        roots = valid_real_roots(poly)
        if len(roots) == 0:
            return max_lag_rel
        return max(roots)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        try:
            pfit, pcov = opt.curve_fit(
                apoly, lag_mesh, like_mesh,
                self.apoly_init(lag_mesh, like_mesh),
                bounds = self.apoly_bounds(lag_mesh),
            )
        except RuntimeError:
            return self.default_estimate(lag_mesh)

        peak_lag, peak_like, *arms_interleaved = pfit

        coeffs_lo, coeffs_hi = zip(*iter_pairs(arms_interleaved))

        min_lag, max_lag = self.lag_range(lag_mesh)
        lag_conf_range = self.find_err(coeffs_lo, peak_lag - min_lag), self.find_err(coeffs_hi, max_lag - peak_lag)

        return {
            'dt': peak_lag,
            'dt_err': lag_conf_range,
            'fit_params': pfit,
            'like_fit': lambda x: apoly(x, *pfit)
        }