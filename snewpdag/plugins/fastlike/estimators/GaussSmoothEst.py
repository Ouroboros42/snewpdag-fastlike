"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from sys import float_info
from typing import Callable

from .EstimatorBase import EstimatorBase

class GaussSmoothEst(EstimatorBase):
    def __init__(self, gauss_width: float, **kwargs):
        self.gauss_width = gauss_width
        super().__init__(**kwargs)

    def smoothed_loglikelihood_func(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> Callable[[float], float]:
        @np.vectorize
        def smoothed_likelihood(lag: float):
            diff_scaled = (lag - lag_mesh) / self.gauss_width
            weights = np.exp(diff_scaled ** 2 / -2)
            return np.average(like_mesh, weights=weights)
        return smoothed_likelihood

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        smoothed_like = self.smoothed_loglikelihood_func(lag_mesh, like_mesh)

        init_guess = lag_mesh[np.argmax(like_mesh)]

        opt_result = opt.minimize(lambda x: -smoothed_like(x), np.array((init_guess,)),
            method='L-BFGS-B',
            bounds=((np.min(lag_mesh), np.max(lag_mesh)),)
        )

        peak_time = opt_result.x.item()
        neg_second_deriv = (opt_result.hess_inv * np.ones(1)).item()

        return {
            'dt': peak_time,
            'var': neg_second_deriv,
            'like_fit': smoothed_like
        }

