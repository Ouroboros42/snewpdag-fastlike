"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike

from .cum_util import lag_estimate
from .EstimatorBase import EstimatorBase

class CumProbEst(EstimatorBase):
    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        return lag_estimate(lags, log_likelihoods)
