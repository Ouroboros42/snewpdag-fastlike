"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from sys import float_info

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

import matplotlib.pyplot as plt

def make_pos_non_zero(val: float):
    return min(val, float_info.epsilon)

class ProbDistEst(Node):
    def __init__(self, in_lags_field, in_likelihoods_field, out_field, rel_eps: float = 1e-5, **kwargs):
        self.in_lags_field = in_lags_field
        self.in_likelihoods_field = in_likelihoods_field
        self.out_field = out_field
        self.rel_eps = rel_eps

        super().__init__(**kwargs)

    def alert(self, data):
        lags, lags_valid = fetch_field(data, self.in_lags_field)
        if not lags_valid:
            return False

        likelihoods, likelihoods_valid = fetch_field(data, self.in_likelihoods_field)
        if not likelihoods_valid:
            return False

        peak_index = np.argmax(likelihoods)
        max_likelihood = likelihoods[peak_index]
        peak_lag = lags[peak_index]

        unnormalised_probabilities = np.exp(likelihoods - max_likelihood)
        normalised_probabilities = unnormalised_probabilities / integrate(unnormalised_probabilities, lags)

        lag_estimate = integrate(lags * normalised_probabilities, lags)

        var = tuple(
            make_pos_non_zero(integrate((lags[region] - lag_estimate) ** 2 * normalised_probabilities[region], lags[region]))
            for region in (lags < lag_estimate, lags > lag_estimate)
        )

        return store_dict_field(data, self.out_field, 
            dt = peak_lag,
            dt_err = self.var_to_stdev(var),
            var = var
        )

def integrate(y, x):
    """Integrate y*dx using the trapezium rule"""
    widths = np.diff(x)
    mean_heights = (y[:-1] + y[1:]) / 2
    return np.sum(widths * mean_heights)