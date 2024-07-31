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

class PolyFitLag(Node):
    def __init__(self, in_field, out_field, mesh_spacing: float, poly_degree: int = 10, **kwargs):
        self.mesh_spacing = mesh_spacing
        self.in_field = in_field
        self.out_field = out_field
        self.poly_degree = poly_degree
        self.max_lag = kwargs.pop('max_lag', 0.1)

        super().__init__(**kwargs)

    @staticmethod
    def poly_domain_check(x: ArrayLike, poly: Polynomial):
        lo, hi = poly.domain
        return (lo <= x) & (x <= hi)

    def find_peak(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> tuple[float, float]:
        pfit = Polynomial.fit(lag_mesh, like_mesh, deg=self.poly_degree)
        pderiv = pfit.deriv()
        
        extrema = pderiv.roots()
        real_extrema = np.real(extrema[np.isreal(extrema)])
        valid_extrema = real_extrema[self.poly_domain_check(real_extrema, pfit)]
        
        extrema_likelihoods = pfit(valid_extrema)

        peak_index = np.argmax(extrema_likelihoods)
        peak_time = valid_extrema[peak_index]
        second_deriv = pderiv.deriv()
        fisher_info = -second_deriv(peak_time)
        if fisher_info < 0:
            logger.warning("Likelihood maximum not found - positive second derivative")
        stddev = np.sqrt(1 / np.abs(fisher_info))

        return peak_time, stddev, pfit

    def alert(self, data):
        binning, is_binning_valid = fetch_field(data, self.in_field)
        if not is_binning_valid:
            return False

        lag_mesh = np.arange(-self.max_lag, self.max_lag, self.mesh_spacing)
        like_mesh = binning['get_log_likelihood'](lag_mesh)

        peak_lag, lag_uncertainty, poly_fit = self.find_peak(lag_mesh, like_mesh)

        return store_dict_field(data, self.out_field, 
            dt = peak_lag,
            dt_err = lag_uncertainty,
            var = lag_uncertainty ** 2,
            mesh = {
                "lags": lag_mesh,
                "log_likelihoods": like_mesh
            }
        )