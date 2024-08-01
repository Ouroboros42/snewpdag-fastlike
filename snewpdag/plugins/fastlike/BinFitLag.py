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
from scipy.special import gammaln
from sys import float_info

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

import matplotlib.pyplot as plt


GT_ZERO = float_info.epsilon
GT_ONE = 1 + float_info.epsilon
INF = 1e8

def log_factorial(x):
    return gammaln(x + 1)

def binwise_poisson_log_likelihood(rates, counts):
    return np.sum(-rates + counts * np.log(rates) - log_factorial(counts))

class BinFitLag(Node):
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
            lag, bg1, bg2, sens2 = p[:4]
            bin_rates = p[4:]
            hist_1 = binning['hist_1']
            hist_2 = binning['get_hist_2'](lag)

            tot_rates_1 = bin_rates + bg1
            tot_rates_2 = bin_rates * sens2 + bg2

            # print(f"Lowest rates: {np.min(tot_rates_1):.4g}, {np.min(tot_rates_2):.4g}")
            # print(f"Highest rates: {np.max(tot_rates_1):.4g}, {np.max(tot_rates_2):.4g}")

            log_likelihood = binwise_poisson_log_likelihood(tot_rates_1, hist_1) + binwise_poisson_log_likelihood(tot_rates_2, hist_2)
            likelihoods.append(log_likelihood)
            return -log_likelihood
        
        infeasibly_large_rate = np.sum(binning['hist_1'])

        param_bounds = (
            (-self.max_lag, self.max_lag), # Lag
            (GT_ZERO, infeasibly_large_rate), # Bg 1
            (GT_ZERO, infeasibly_large_rate), # Bg 2
            (GT_ZERO, infeasibly_large_rate), # Sensitvity ratio 2 to 1
        ) + binning['n_bins'] * ((GT_ZERO, infeasibly_large_rate),) # Bin rate (1)

        # bg_1_init = 1e-2
        # bg_2_init = 1e-3
        # rate_init = np.minimum(binning['hist_1'] - bg_1_init, GT_ZERO)
        # sens_init = np.minimum(np.mean((binning['hist_2'] - bg_2_init) / rate_init), GT_ZERO)

        # initial = np.concatenate((np.array([0, bg_1_init, bg_2_init, sens_init]), rate_init))

        opt_result = opt.dual_annealing(
            neg_log_likelihood,
            param_bounds,
            initial_temp=100,
            no_local_search=True,
        )

        likelihoods = np.array(likelihoods)
        params = np.array(params)
        
        cut = likelihoods > np.quantile(likelihoods, 0.9)
        likelihoods = likelihoods[cut]
        params = params[cut, :]

        lags = params[:,0]

        inds = lags.argsort()
        lags = lags[inds]
        likelihoods = likelihoods[inds]
        bg_1_est = params[inds, 1]
        bg_2_est = params[inds, 2]
        sens_est = params[inds, 3]
        bin_rate_ests = params[inds, 4:]

        peak_lag = opt_result.x[0]
        unnormalised_probabilities = np.exp(likelihoods + opt_result.fun)
        normalised_probabilities = unnormalised_probabilities / integrate(unnormalised_probabilities, lags)

        plot_tdist("/data/snoplus/lucas/snout/temp/tdist.png", opt_result.x[4:], binning['original_edges'])

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

def plot_tdist(filename, rates, edges, **kwargs):
    fig, ax = plt.subplots()
    ax.stairs(rates, edges, baseline=None, **kwargs) 
    fig.savefig(filename, dpi=1000, bbox_inches='tight')
    plt.close(fig)