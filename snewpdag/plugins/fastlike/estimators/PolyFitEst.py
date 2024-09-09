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
from .poly_util import find_peak, weights

class PolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree, w=weights(self.curve_weights, like_mesh))
        
        peak_time, peak_like = find_peak(pfit)

        second_deriv = pfit.deriv().deriv()
        fisher_info = -second_deriv(peak_time)
        
        if fisher_info < 0:
            logging.warning(f"Likelihood maximum not found - positive second derivative in {self.name}")

        var = 1 / np.abs(fisher_info)

        return {
            'dt': peak_time,
            'var': var,
            'like_fit': pfit
        }