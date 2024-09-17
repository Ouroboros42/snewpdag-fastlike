"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt
from scipy.special import expit as sigmoid

from .EstimatorBase import EstimatorBase
from .poly_util import find_peak, weights

class QuadFitEst(EstimatorBase):
    def __init__(self, use_raw_peak=False, fit_cost="quad", **kwargs):
        self.use_raw_peak = use_raw_peak
        self.fit_cost = fit_cost
        super().__init__(**kwargs)

    def quad_fit(self, lags, mean_lag, lag_var, max_like):
        return max_like - (lags - mean_lag)**2 / (2 * lag_var)
    
    fit_costs = {
        "quad": lambda x, x_fit: (x - x_fit) ** 2,
        "exp_quad": lambda x, x_fit: (np.exp(x) - np.exp(x_fit))**2,
        "sig_quad": lambda x, x_fit: (x - x_fit) ** 2 * sigmoid(np.maximum(x, x_fit))
    }

    def error_cost(self, like_mesh, like_fit):
        log_rescale = max(np.max(like_mesh), np.max(like_fit))
        like_mesh -= log_rescale
        like_fit -= log_rescale

        return np.sum(self.fit_costs[self.fit_cost](like_mesh, like_fit))

    def init_params(self, lag_mesh, like_mesh, peak_lag, peak_like):
        default_var = self.max_var(lag_mesh) / 2
        default_max = peak_like

        params = [default_var, default_max]

        if not self.use_raw_peak:
            default_peak = 0
            params = [default_peak] + params

        return np.array(params)
    
    def param_bounds(self, lag_mesh, like_mesh, peak_lag, peak_like):
        var_bounds = self.min_var(lag_mesh), self.max_var(lag_mesh)
        max_bounds = np.min(like_mesh), np.max(like_mesh)

        bounds = [var_bounds, max_bounds]

        if not self.use_raw_peak:
            peak_bounds = np.min(lag_mesh), np.max(lag_mesh)
            bounds = [peak_bounds] + bounds

        return bounds

    def cost_function(self, params, lag_mesh, like_mesh, peak_lag, peak_like):
        like_fit = self.quad_fit(lag_mesh, peak_lag, *params) if self.use_raw_peak else self.quad_fit(lag_mesh, *params)

        return self.error_cost(like_mesh, like_fit)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        peak_i = np.argmax(like_mesh)
        peak_lag = lag_mesh[peak_i]
        peak_like = like_mesh[peak_i]

        args = lag_mesh, like_mesh, peak_lag, peak_like
        res = opt.minimize(self.cost_function, self.init_params(*args), args=args, bounds=self.param_bounds(*args))
        params = tuple(res.x)
        if self.use_raw_peak:
            params = (peak_lag,) + params

        def like_fit(lags):
            return self.quad_fit(lags, *params)

        lag_estimate, lag_var, max_like = params

        return {
            'dt': lag_estimate,
            'var': lag_var,
            'like_fit': like_fit
        }