import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from math import sqrt

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

def poly(x: ArrayLike, peak_x: float, peak_y: float, *coefficients_quadplus: float):
    return peak_y + sum(c * ((x - peak_x) ** (n + 2)) for n, c in enumerate(coefficients_quadplus))

class BoundedPolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def poly_bounds(self, min_lag, max_lag):
        n_extra_terms = self.poly_degree - 2

        # Quadratic term must be negative at peak
        upper = np.array([max_lag,  np.inf,  0      ] + [  np.inf ] * n_extra_terms) 
        lower = np.array([min_lag, -np.inf, -np.inf ] + [ -np.inf ] * n_extra_terms)

        return lower, upper

    def poly_init(self, peak_like):
        return np.array([0, peak_like] + [0] * (self.poly_degree - 1))

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        max_like = np.max(like_mesh)

        min_lag = np.min(lag_mesh)
        max_lag = np.max(lag_mesh)

        fit_params, fit_cov = opt.curve_fit(poly, lag_mesh, like_mesh,
            p0=self.poly_init(max_like), bounds=self.poly_bounds(min_lag, max_lag)
        )

        domain = np.array([min_lag, max_lag])
        window = domain - fit_params[0]
        fit_poly = Polynomial([fit_params[1], 0, *fit_params[2:]], domain, window)

        peak_lag, peak_like = find_peak(fit_poly)
        second_deriv = fit_poly.deriv().deriv()

        stdev = self.curve_uncertainty(second_deriv(peak_lag))

        def like_fit(lag):
            return poly(lag, *fit_params)

        return {
            'dt': peak_lag,
            'dt_err': stdev,
            'like_fit': like_fit
        }