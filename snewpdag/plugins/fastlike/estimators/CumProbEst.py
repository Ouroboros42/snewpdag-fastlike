"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from sys import float_info

from .EstimatorBase import EstimatorBase

class CumProbEst(EstimatorBase):
    CLOSE_ENOUGH_ZERO = float_info.epsilon
    CLOSE_ENOUGH_ONE = 1 - float_info.epsilon

    @staticmethod
    def cum_integrate(y, x):
        """Integrate y*dx using the trapezium rule, assuming x is ordered"""
        widths = np.diff(x)
        rects = widths * (y[:-1] + y[1:]) / 2
        
        out = np.empty_like(y)
        out[0] = 0
        np.cumsum(rects, out=out[1:])
        return out
    
    @staticmethod
    def lerp(x0, x1, y0, y1, x_target):
        return float((y1 - y0) / (x1 - x0) * (x_target - x0) + y0)

    @staticmethod
    def interpolate(x, y, x_target):
        """Assumes monotonically increasing"""
        exact_hits = np.nonzero(x == x_target)[0]

        if len(exact_hits):
            return np.median(y[exact_hits])

        before = np.nonzero(x < x_target)[0]
        if len(before) == 0:
            return y[0]
        if len(before) == len(x):
            logging.warning("Upper bound broken")
            return y[-1]

        last_before = before[-1]

        return CumProbEst.lerp(x[last_before], x[last_before+1], y[last_before], y[last_before+1], x_target)

    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        peak_index = np.argmax(log_likelihoods)
        max_log_likelihood = log_likelihoods[peak_index]
        peak_lag = lags[peak_index]

        likelihoods = np.exp(log_likelihoods - max_log_likelihood)
        cum_likelihood = self.cum_integrate(likelihoods, lags)
        cum_probability = cum_likelihood / cum_likelihood[-1]
        
        # print(lags)
        # print(cum_probability)

        median_lag = self.interpolate(cum_probability, lags, 0.5)
        
        low_bound_cum_prob = 0.5 - self.ONESIDE_CONFIDENCE_RANGE
        high_bound_cum_prob = 0.5 + self.ONESIDE_CONFIDENCE_RANGE

        low_bound = self.interpolate(cum_probability, lags, low_bound_cum_prob)
        high_bound = self.interpolate(cum_probability, lags, high_bound_cum_prob)

        if min(abs(low_bound - lags[0]), abs(high_bound - lags[-1])) < float_info.epsilon:
            logging.warning(f"Bound finding broken\n{cum_probability=}")

        dt_err = (median_lag - low_bound, high_bound - median_lag)

        return { 
            'dt': median_lag,
            'dt_err': dt_err
        }
