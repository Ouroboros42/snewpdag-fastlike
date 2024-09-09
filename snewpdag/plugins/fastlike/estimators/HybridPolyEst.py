import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from math import sqrt

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

class HybridPolyEst(EstimatorBase):
    def __init__(self, poly_degree=10, shift_errors=False, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.shift_errors = shift_errors
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree, w=weights(self.curve_weights, like_mesh))

        second_deriv = pfit.deriv().deriv()

        peak_time = lag_mesh[np.argmax(like_mesh)]

        deriv_point, _ = find_peak(pfit)

        fisher_info = -second_deriv(deriv_point)
        if fisher_info < 0:
            logging.warning("Likelihood maximum not found - positive second derivative")

        stdev = sqrt(1 / abs(fisher_info))

        if self.shift_errors:
            err_shift = peak_time - deriv_point
            uncertainty = sqrt(stdev ** 2 + err_shift ** 2)
        else:
            uncertainty = stdev

        return {
            'dt': peak_time,
            'dt_err': uncertainty,
            'like_fit': pfit
        }