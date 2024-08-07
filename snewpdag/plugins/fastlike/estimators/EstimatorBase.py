"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike

from abc import ABCMeta, abstractmethod

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

class EstimatorBase(Node, metaclass=ABCMeta):
    def __init__(self, in_lags_field, in_likelihoods_field, out_field, **kwargs):
        self.in_lags_field = in_lags_field
        self.in_likelihoods_field = in_likelihoods_field
        self.out_field = out_field
        super().__init__(**kwargs)

    @abstractmethod
    def estimate_lag(self, lags: np.ndarray[float], log_likelihoods: np.ndarray[float]) -> dict:
        pass

    @staticmethod
    def is_sorted(arr: np.ndarray):
        return np.all(arr[:-1] <= arr[1:])

    @staticmethod
    def var_to_stdev(var):
        return tuple(np.sqrt(var))
    
    @staticmethod
    def stdev_to_var(stdev):
        return tuple(np.square(stdev))

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

        return store_dict_field(data, self.out_field, **self.estimate_lag(lags, likelihoods))