import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from math import sqrt

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

class FixedPolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        peak_time = lag_mesh[np.argmax(like_mesh)]

        pdomain = np.min(lag_mesh), np.max(lag_mesh)
        pwindow = tuple(t - peak_time for t in pdomain)
        pdeg = (0, *range(2,self.poly_degree+1)) # No linear term means there must be a peak at 0 (which is really at peak_time due to window)

        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=pdeg, domain=pdomain, window=pwindow, w=weights(self.curve_weights, like_mesh))

        second_deriv = pfit.deriv().deriv()

        stdev = self.curve_uncertainty(pfit.coef[2])

        return {
            'dt': peak_time,
            'dt_err': stdev,
            'like_fit': pfit
        }