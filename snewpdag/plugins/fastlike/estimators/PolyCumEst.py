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
from .poly_util import weights
from .cum_util import lag_estimate

class PolyCumEst(EstimatorBase):
    def __init__(self, poly_degree=10, integral_samples=10000, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.curve_weights = curve_weights
        self.integral_samples = integral_samples
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree, w=weights(self.curve_weights, like_mesh))
    
        sample_lags = np.linspace(np.min(lag_mesh), np.max(lag_mesh), self.integral_samples)
        sample_likes = pfit(sample_lags)        

        return {
            **lag_estimate(sample_lags, sample_likes),
            'like_fit': pfit
        }