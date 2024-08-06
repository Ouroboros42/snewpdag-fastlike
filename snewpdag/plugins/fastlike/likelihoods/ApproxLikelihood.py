from .LikelihoodBase import LikelihoodBase

import logging
import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial
from scipy.special import loggamma

from sys import float_info

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

class ApproxLikelihood(LikelihoodBase):
    def log_likelihood(self, hist_2: np.ndarray[float], hist_1: np.ndarray[float], detectors: DetectorRelation) -> float:
        ar = 1 / (1 + detectors.sensitivity_ratio_2_to_1)
        pr = 1 - ar

        b, q = detectors.bin_background_rates

        return np.sum(find_bin_log_likelihood(hist_1, hist_2, ar, pr, b, q))

def bin_log_likelihood(n, m, ar, pr, b, q, rate):
    rate = np.maximum(rate, 0)
    return - (rate + b + q) + n * np.log(ar * rate + b) + m * np.log(pr * rate + q) - loggamma(n+1) - loggamma(m+1)

def solve_quadratic(a, b, c):
    half_b = b/2
    root_discriminant = np.sqrt(half_b * half_b - a * c)

    b_sign = (-1) ** (b < 0)
    ax = -(half_b + b_sign * root_discriminant)

    return ax / a, c / ax

def find_bin_log_likelihood(n, m, ar, pr, b, q):
    peak_root_1, peak_root_2 = solve_quadratic(
        ar * pr,
        ar * q + pr * b - (n + m) * ar * pr,
        b * q - ar * q * n - pr * b * m
    )

    return np.maximum(
        bin_log_likelihood(n, m, ar, pr, b, q, peak_root_1),
        bin_log_likelihood(n, m, ar, pr, b, q, peak_root_2),
    )

    