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
from .poly_util import valid_real_roots

from itertools import islice

def take_alternate(iterable, take_odd: bool):
    """Take every other element of iterable, starting at index 1 if take_odd is True"""
    return islice(iterable, int(take_odd), None, 2)

def polynomial(x: float, lowest_exponent: int, coefficients_ascending):
    return sum(c * (x ** (n + lowest_exponent)) for n, c in enumerate(coefficients_ascending))

def polynomialderiv(x: float, lowest_exponent: int, coefficients_ascending):
    return polynomial(x, lowest_exponent - 1, ((n + lowest_exponent) * c for n, c in enumerate(coefficients_ascending)))

@np.vectorize
def apoly(x: float, peak_x: float, peak_y: float, *arms_interleaved: float):
    diff = x - peak_x
    return peak_y + polynomial(abs(diff), 2, take_alternate(arms_interleaved, diff > 0))

@np.vectorize
def apolyderiv(x: float, peak_x: float, peak_y: float, *arms_interleaved: float):
    diff = x - peak_x
    return polynomialderiv(abs(diff), 2, take_alternate(arms_interleaved, diff > 0))

# @np.vectorize(signature='()->(n)')
# def apolyjac(x: float, peak_x: float, peak_y: float, *arms_interleaved: float):
#     return np.array([
#         - apolyderiv(x, peak_x, peak_y, *arms_interleaved),
#         1.0,
#     ] + [
#         x ** (n // 2 + 2) if (x > peak_x == bool(n % 2)) else 0 \
#         for n in range(len(arms_interleaved))
#     ])

class APolyFitEst(EstimatorBase):
    def __init__(self, poly_degree=10, **kwargs):
        self.poly_terms = poly_degree - 1
        super().__init__(**kwargs)

    def apoly_bounds(self, lag_mesh):
        n_extra_terms = 2 * (self.poly_terms - 1)

        # Quadratic terms must be negative at peak
        lower = np.array([ np.min(lag_mesh), -np.inf, -np.inf, -np.inf ] + [ -np.inf ] * n_extra_terms)
        upper = np.array([ np.max(lag_mesh),  np.inf,  0     ,  0      ] + [  np.inf ] * n_extra_terms) 

        return lower, upper

    def apoly_init(self, lag_mesh, like_mesh):
        peak_index = np.argmax(like_mesh)
        max_log_likelihood = like_mesh[peak_index]
        peak_lag = lag_mesh[peak_index]

        return np.array([ peak_lag, max_log_likelihood ] + [0] * (self.poly_terms * 2))

    def estimate_lag(self, lag_mesh: np.ndarray[float], like_mesh: np.ndarray[float]) -> dict:
        pfit, pcov = opt.curve_fit(
            apoly, lag_mesh, like_mesh,
            self.apoly_init(lag_mesh, like_mesh),
            bounds = self.apoly_bounds(lag_mesh),
            # jac = apolyjac
        )
        
        peak_lag, peak_like, low_quad_term, high_quad_term, *_ = pfit

        var = (-1/low_quad_term, -1/high_quad_term)

        return {
            'dt': peak_lag,
            'var': var,
            'like_fit': lambda x: apoly(x, *pfit)
        }