import numpy as np
from numpy.typing import ArrayLike
from scipy.integrate import cumulative_trapezoid
from sys import float_info

ONESIDE_CONFIDENCE_RANGE = 0.341344746069
CUMPROB_POINTS = 0.5 + np.array((-ONESIDE_CONFIDENCE_RANGE, 0, +ONESIDE_CONFIDENCE_RANGE))

EPSILON= float_info.epsilon

def cum_prob_from_log_likelihoods(lags: ArrayLike, log_likelihoods: ArrayLike) -> np.ndarray:
    likelihoods = np.exp(log_likelihoods - np.max(log_likelihoods))
    unscaled_cumprobs = cumulative_trapezoid(likelihoods, lags, initial=0)
    return unscaled_cumprobs / unscaled_cumprobs[-1]

def median_and_bounds(lags: ArrayLike, log_likelihoods: ArrayLike):
    cumprobs = cum_prob_from_log_likelihoods(lags, log_likelihoods)
    
    low_bound, median, high_bound = np.interp(CUMPROB_POINTS, cumprobs, lags)
    
    return median, (low_bound, high_bound)

def lag_estimate(lags: ArrayLike, log_likelihoods: ArrayLike):
    median, (low_bound, high_bound) = median_and_bounds(lags, log_likelihoods)
    
    if (low_bound - lags[0]) / abs(lags[0]) < EPSILON or (lags[-1] - high_bound) / abs(lags[-1]) < EPSILON:
        logging.warning(f"Cumulative probability gave bound very close to edge of lag range, possible error.\n{cum_probability=} {low_bound=} {high_bound=}")

    return {
        "dt": median,
        "dt_err": (abs(low_bound - median), abs(high_bound - median))
    }

    