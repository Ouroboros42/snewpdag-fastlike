import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from math import sqrt

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

def poly(x: ArrayLike, peak_y: float, *coefficients_quadplus: float):
    return peak_y + sum(c * (x ** (n + 2)) for n, c in enumerate(coefficients_quadplus))

class FixedPolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def poly_bounds(self):
        n_extra_terms = self.poly_degree - 2

        # Quadratic term must be negative at peak
        upper = np.array([ np.inf,  0      ] + [  np.inf ] * n_extra_terms) 
        lower = np.array([-np.inf, -np.inf ] + [ -np.inf ] * n_extra_terms)

        return lower, upper

    def poly_init(self, peak_like):
        return np.array([peak_like] + [0] * (self.poly_degree - 1))

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        peak_i = np.argmax(like_mesh)
        peak_lag = lag_mesh[peak_i]
        peak_like = like_mesh[peak_i]
        zeroed_lags = lag_mesh - peak_lag

        fit_params, fit_cov = opt.curve_fit(poly, zeroed_lags, like_mesh,
            p0=self.poly_init(peak_like), bounds=self.poly_bounds()
        )

        stdev = self.curve_uncertainty(2 * fit_params[1])

        def like_fit(lag):
            return poly(lag - peak_lag, *fit_params)

        return {
            'dt': peak_lag,
            'dt_err': stdev,
            'like_fit': like_fit
        }