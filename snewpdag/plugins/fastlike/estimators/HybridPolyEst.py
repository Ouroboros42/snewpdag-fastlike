import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

class HybridPolyEst(EstimatorBase):
    def __init__(self, poly_degree=10, use_poly_peak_deriv=False, curve_weights=None, **kwargs):
        self.poly_degree = poly_degree
        self.use_poly_peak_deriv = use_poly_peak_deriv
        self.curve_weights = curve_weights
        super().__init__(**kwargs)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree, w=weights(self.curve_weights, like_mesh))

        second_deriv = pfit.deriv().deriv()

        peak_time = lag_mesh[np.argmax(like_mesh)]

        if self.use_poly_peak_deriv:
            deriv_point, _ = find_peak(pfit)
        else:
            deriv_point = peak_time

        fisher_info = -second_deriv(deriv_point)
        if fisher_info < 0:
            logging.warning("Likelihood maximum not found - positive second derivative")

        var = 1 / np.abs(fisher_info)

        return {
            'dt': peak_time,
            'var': var,
            'like_fit': pfit
        }