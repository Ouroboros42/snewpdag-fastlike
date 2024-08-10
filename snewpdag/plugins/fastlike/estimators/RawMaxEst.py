"""
"""
import logging
import numpy as np

from .EstimatorBase import EstimatorBase

class RawMaxEst(EstimatorBase):
    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        peak_i = np.argmax(log_likelihoods)
        peak_lag = lags[peak_i]

        peak_likelihood = log_likelihoods[peak_i]
        err_drop = peak_likelihood - 0.5

        conf_range_lags = lags[log_likelihoods > err_drop]

        low_bound = min(lags.take(peak_i - 1, mode='clip'), conf_range_lags[0])
        high_bound = max(lags.take(peak_i + 1, mode='clip'), conf_range_lags[-1])

        dt_err = (peak_lag - low_bound, high_bound - peak_lag)

        return { 
            'dt': peak_lag,
            'dt_err': dt_err
        }
