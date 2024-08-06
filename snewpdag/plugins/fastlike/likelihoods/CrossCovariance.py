from .LikelihoodBase import LikelihoodBase

import logging
import numpy as np
from numpy.typing import ArrayLike

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation, FactorialCache

class CrossCovariance(LikelihoodBase):
    def log_likelihood(self, hist_2: np.ndarray[float], hist_1: np.ndarray[float], detectors: DetectorRelation) -> float:
        bg_1, bg_2 = detectors.bin_background_rates
        norm_hist_1 = (hist_1 - bg_1) * detectors.sensitivity_ratio_2_to_1
        norm_hist_2 = hist_2 - bg_2
        return np.sum(norm_hist_1 * norm_hist_2)