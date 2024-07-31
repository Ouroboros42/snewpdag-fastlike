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
from sys import float_info

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

import matplotlib.pyplot as plt


GT_ZERO = float_info.epsilon
GT_ONE = 1 + float_info.epsilon
INF = 1e8

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

        params = []
        likelihoods = []

        def neg_log_likelihood(p):
            params.append(p)
            lag = p[0]
            other_params = p[1:]     
            log_likelihood = binning['get_log_likelihood'](lag, DetectorRelation(*other_params)).item()
            likelihoods.append(log_likelihood)
            return -log_likelihood

        opt_result = opt.dual_annealing(
            neg_log_likelihood,
            ((-self.max_lag, self.max_lag), (GT_ZERO, INF), (GT_ZERO, INF), (GT_ZERO, INF), (GT_ONE, INF)),
            initial_temp=10000,
            # minimizer_kwargs = {
            #     method = lambda 
            # }
        )

        params = np.array(params)
        likelihoods = np.array(likelihoods)
        lags = params[:,0]

        inds = lags.argsort()
        lags = lags[inds]
        likelihoods = likelihoods[inds]
        params = params[inds,1:]

        peak_lag = opt_result.x[0]
        peak_k = opt_result.x[-1]
        print(f"{peak_k=:.5g}")
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