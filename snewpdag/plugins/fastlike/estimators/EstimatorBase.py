"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike

from abc import ABCMeta, abstractmethod

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

from sys import float_info

from .cum_util import EPSILON, ONESIDE_CONFIDENCE_RANGE

def clamp(x, lo, hi):
    return min(hi, max(lo, x))

class EstimatorBase(Node, metaclass=ABCMeta):
    EPSILON = EPSILON
    FULL_CONFIDENCE_RANGE = 2 * ONESIDE_CONFIDENCE_RANGE

    def __init__(self, in_lags_field, in_likelihoods_field, out_field, **kwargs):
        self.in_lags_field = in_lags_field
        self.in_likelihoods_field = in_likelihoods_field
        self.out_field = out_field
        super().__init__(**kwargs)

    def default_estimate(self, lag_mesh):
        return  {
            'dt': 0,
            'dt_err': self.max_errs(lag_mesh)
        }
    
    def lag_range(self, lag_mesh):
        return np.min(lag_mesh), np.max(lag_mesh)
    
    def max_lag(self, lag_mesh):
        return max(map(abs, self.lag_range(lag_mesh)))

    def max_errs(self, lag_mesh):
        lo_lag, hi_lag = self.lag_range(lag_mesh)
        return self.FULL_CONFIDENCE_RANGE * abs(lo_lag), self.FULL_CONFIDENCE_RANGE * abs(hi_lag)

    def max_var(self, lag_mesh):
        return max(self.max_errs(lag_mesh))**2

    def min_var(self, lag_mesh):
        return self.EPSILON * abs(np.max(lag_mesh) - np.min(lag_mesh))

    @abstractmethod
    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        pass

    @staticmethod
    def is_sorted(arr: np.ndarray):
        return np.all(arr[:-1] <= arr[1:])

    @staticmethod
    def arr_to_tup_or_scalar(a: np.ndarray):
        return tuple(a) if a.shape else a.item()

    @staticmethod
    def var_to_stdev(var):
        return EstimatorBase.arr_to_tup_or_scalar(np.sqrt(var))
    
    @staticmethod
    def stdev_to_var(stdev):
        return EstimatorBase.arr_to_tup_or_scalar(np.square(stdev))

    def alert(self, data):
        lags, is_lags_valid = fetch_field(data, self.in_lags_field)
        if not is_lags_valid:
            return False

        likelihoods, is_likelihoods_valid = fetch_field(data, self.in_likelihoods_field)
        if not is_likelihoods_valid:
            return False

        if not self.is_sorted(lags):
            sort_i = lags.argsort()
            lags = lags[sort_i]
            likelihoods = likelihoods[sort_i]
        
        result = self.estimate_lag(lags, likelihoods)

        result['dt'] = clamp(result['dt'], *self.lag_range(lags))

        if 'var' in result and 'dt_err' not in result:
            result['dt_err'] = self.var_to_stdev(result['var'])

        min_err = self.max_lag(lags) * self.EPSILON
        lo_max_err, hi_max_err = self.max_errs(lags)

        if isinstance(result['dt_err'], (list, tuple)):
            lo_err, hi_err = result['dt_err']
            result['dt_err'] = clamp(lo_err, min_err, lo_max_err), clamp(hi_err, min_err, hi_max_err)
        else:
            max_err = max(lo_max_err, hi_max_err)
            result['dt_err'] = clamp(result['dt_err'], min_err, max_err)

        result['var'] = self.stdev_to_var(result['dt_err'])

        return store_dict_field(data, self.out_field, **result)