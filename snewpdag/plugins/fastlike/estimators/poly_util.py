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
        