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

class PolyCumEst(EstimatorBase):
    ONESIDE_CONFIDENCE_RANGE = 0.341344746069
    EST_CUM_PROB = 0.5
    LOW_BOUND_CUM_PROB = EST_CUM_PROB - ONESIDE_CONFIDENCE_RANGE
    HIGH_BOUND_CUM_PROB = EST_CUM_PROB + ONESIDE_CONFIDENCE_RANGE

    def __init__(self, poly_degree=10, **kwargs):
        self.poly_degree = poly_degree
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], log_like_mesh: np.ndarray[float]) -> dict:
        like_mesh = np.exp(log_like_mesh - np.max(log_like_mesh))

        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree)
        cum_like = pfit.integ(lbnd=np.min(lag_mesh))
        cum_prob = cum_like / cum_like(np.max(lag_mesh))

        median_lag = valid_real_roots(cum_prob - self.EST_CUM_PROB).item()
        low_bound = valid_real_roots(cum_prob - self.LOW_BOUND_CUM_PROB).item()
        high_bound = valid_real_roots(cum_prob - self.HIGH_BOUND_CUM_PROB).item()

        dt_err = (median_lag - low_bound, high_bound - median_lag)
        var = tuple(np.square(dt_err))

        return {
            'dt': median_lag,
            'dt_err': dt_err,
            'var': var
        }