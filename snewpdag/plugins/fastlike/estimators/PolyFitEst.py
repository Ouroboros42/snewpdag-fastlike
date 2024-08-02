"""
PolyFitLag - estimate burst time from a polynomial fit likelihood of Poisson distributed burst data

Optional:
    poly_degree: degree of polynomial to fit
"""
import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
import scipy.optimize as opt

from .EstimatorBase import EstimatorBase

class PolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, **kwargs):
        self.poly_degree = poly_degree
        super().__init__(**kwargs)

    @staticmethod
    def poly_domain_check(x: ArrayLike, poly: Polynomial):
        lo, hi = poly.domain
        return (lo <= x) & (x <= hi)

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
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

        var = 1 / np.abs(fisher_info)
        stddev = np.sqrt(var)

        return {
            'dt': peak_time,
            'dt_err': stddev,
            'var': var
        }