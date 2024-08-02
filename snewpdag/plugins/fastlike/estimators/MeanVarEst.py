"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from sys import float_info

from .EstimatorBase import EstimatorBase

def make_pos_non_zero(val: float):
    return min(val, float_info.epsilon)

class MeanVarEst(EstimatorBase):
    @staticmethod
    def integrate(y, x):
        """Integrate y*dx using the trapezium rule"""
        widths = np.diff(x)
        mean_heights = (y[:-1] + y[1:]) / 2
        return np.sum(widths * mean_heights)

    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        peak_index = np.argmax(log_likelihoods)
        max_log_likelihood = log_likelihoods[peak_index]
        peak_lag = lags[peak_index]

        likelihoods = np.exp(log_likelihoods - max_log_likelihood)
        probabilities = likelihoods / self.integrate(likelihoods, lags)

        lag_estimate = self.integrate(lags * probabilities, lags)

        var = tuple(
            make_pos_non_zero(self.integrate((lags[region] - lag_estimate) ** 2 * probabilities[region], lags[region]))
            for region in (lags < lag_estimate, lags > lag_estimate)
        )

        return { 
            'dt': peak_lag,
            'dt_err': tuple(np.sqrt(var)),
            'var': var
        }
