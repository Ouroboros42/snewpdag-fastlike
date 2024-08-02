from .LikelihoodBase import LikelihoodBase

import logging
import numpy as np
from numpy.typing import ArrayLike

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation, FactorialCache

class SumLikelihood(LikelihoodBase):
    def __init__(self, rel_precision=1e-2, **kwargs):
        self.rel_precision = rel_precision
        self.fact_cache = FactorialCache()
        super().__init__(**kwargs)

    def log_likelihood(self, hist_2: np.ndarray[float], hist_1: np.ndarray[float], detectors: DetectorRelation) -> float:
        return detectors.log_likelihood(self.fact_cache, hist_1, hist_2, self.rel_precision)
    