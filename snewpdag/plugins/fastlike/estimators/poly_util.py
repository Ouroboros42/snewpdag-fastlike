import numpy as np
from numpy.typing import ArrayLike
from numpy.polynomial import Polynomial

def poly_domain_check(x: ArrayLike, poly: Polynomial):
    lo, hi = poly.domain
    return (lo <= x) & (x <= hi)

def valid_real_roots(poly: Polynomial):
    roots = poly.roots()
    real_roots = np.real(roots[np.isreal(roots)])
    return real_roots[poly_domain_check(real_roots, poly)]

def find_peak(poly: Polynomial):
    roots = valid_real_roots(poly.deriv())
    if len(roots) == 0:
        roots = np.array(poly.domain)
    root_values = poly(roots)
    i_max = np.argmax(root_values)
    return roots[i_max], root_values[i_max]
        

WEIGHT_FORMULAE = {
    None: lambda x: np.ones_like(x),
    'exp': lambda x: np.exp(x - np.max(x)),
    'linear': lambda x: x - np.min(x),
    'inverse': lambda x: 1 / (1 + np.max(x) - x),
    'exphalf': lambda x: np.exp((x - np.max(x)) / 2),
    'inversesquare': lambda x: 1 / (1 + (np.max(x) - x) ** 2),
}

def weights(weight_type, raw_likes: ArrayLike):
    return WEIGHT_FORMULAE[weight_type](raw_likes)