"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt

from .EstimatorBase import EstimatorBase
from .poly_util import valid_real_roots

def iter_pairs(iterable):
    pair_ready = False
    for item in iterable:
        if pair_ready:
            yield np.array((last, item))
        else:
            last = item

        pair_ready = not pair_ready

def signed_diff(diff: ArrayLike):    
    return (diff > 0).astype(int), np.abs(diff)

def apoly(x: ArrayLike, peak_y: float, *arms_interleaved: float):
    is_pos, diff = signed_diff(x)

    return peak_y + sum(c[is_pos] * (diff ** (n + 2)) for n, c in enumerate(iter_pairs(arms_interleaved)))

class FixedAPolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=5, **kwargs):
        self.poly_degree = poly_degree
        super().__init__(**kwargs)

    def apoly_bounds(self):
        n_extra_terms = 2 * (self.poly_degree - 2)

        # Quadratic terms must be negative at peak
        upper = np.array([ np.inf,  0     ,  0      ] + [  np.inf ] * n_extra_terms) 
        lower = np.array([-np.inf, -np.inf, -np.inf ] + [ -np.inf ] * n_extra_terms)

        return lower, upper

    def apoly_init(self, peak_like):
        return np.array([peak_like] + [0] * ((self.poly_degree - 1) * 2))

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        peak_i = np.argmax(like_mesh)
        peak_lag = lag_mesh[peak_i]
        peak_like = like_mesh[peak_i]
        zeroed_lags = lag_mesh - peak_lag
        

        fit_params, fit_cov = opt.curve_fit(apoly, zeroed_lags, like_mesh,
            p0=self.apoly_init(peak_like), bounds=self.apoly_bounds()
        )

        uncertainty = self.curve_uncertainty(tuple(fit_params[1:3]))

        def like_fit(lag):
            return apoly(lag - peak_lag, *fit_params)

        return {
            'dt': peak_lag,
            'dt_err': uncertainty,
            'like_fit': like_fit 
        }