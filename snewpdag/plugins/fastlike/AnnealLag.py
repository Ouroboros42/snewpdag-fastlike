"""
PolyFitLag - estimate burst time from a polynomial fit likelihood of Poisson distributed burst data

Arguments:
    mesh_spacing: spacing of lags to evaluate
    in_field: field which should be the output of HistCompare
    out_field:  output field, will receive a dictionary with (at least) fields:
        dt: most likely time difference
        dt_err: uncertainty in dt estimate
        mesh: all lags for which likelihood has been evaluated
Optional:
    poly_degree: degree of polynomial to fit
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

import matplotlib.pyplot as plt

class AnnealLag(Node):
    def __init__(self, in_field, out_field, mesh_spacing: float, rel_eps: float = 1e-5, **kwargs):
        self.mesh_spacing = mesh_spacing
        self.in_field = in_field
        self.out_field = out_field
        self.rel_eps = rel_eps
        self.max_lag = kwargs.pop('max_lag', 0.1)

        super().__init__(**kwargs)

    def alert(self, data):
        binning, is_binning_valid = fetch_field(data, self.in_field)
        if not is_binning_valid:
            return False

        lags = []
        likelihoods = []
        suppressors = []

        def neg_log_likelihood(t):
            lag=t.item()
            lags.append(lag)
            log_likelihood = binning['get_log_likelihood'](lag).item()
            likelihoods.append(log_likelihood)
            return -log_likelihood

        opt_result = opt.dual_annealing(
            neg_log_likelihood,
            ((-self.max_lag, self.max_lag),),
            initial_temp=10000,
        )

        lags = np.array(lags)
        likelihoods = np.array(likelihoods)

        inds = lags.argsort()
        lags = lags[inds]
        likelihoods = likelihoods[inds]

        peak_lag = opt_result.x.item()
        rescale_factor = opt_result.fun

        unnormalised_probabilities = np.exp(likelihoods + rescale_factor)
        normalised_probabilities = unnormalised_probabilities / integrate(unnormalised_probabilities, lags)

        estimate = integrate(lags * normalised_probabilities, lags)

        var = tuple(
            integrate((lags[region] - estimate) ** 2 * normalised_probabilities[region], lags[region])
            for region in (lags < estimate, lags > estimate)
        )

        return store_dict_field(data, self.out_field, 
            dt = peak_lag,
            dt_err = tuple(np.sqrt(var)),
            var = var,
            mesh = { "lags": lags, "log_likelihoods": likelihoods }
        )

def integrate(y, x):
    """Integrate y*dx using the trapezium rule"""
    widths = np.diff(x)
    mean_heights = (y[:-1] + y[1:]) / 2
    return np.sum(widths * mean_heights)