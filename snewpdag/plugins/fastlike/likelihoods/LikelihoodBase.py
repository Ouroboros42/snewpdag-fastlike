"""
"""
import logging
import numpy as np
from numpy.typing import ArrayLike

from abc import ABCMeta, abstractmethod

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

class LikelihoodBase(Node, metaclass=ABCMeta):
    def __init__(self, in_binning_field, in_mesh_field, out_field, **kwargs):
        self.in_binning_field = in_binning_field
        self.in_mesh_field = in_mesh_field
        self.out_field = out_field
        super().__init__(**kwargs)

    @abstractmethod
    def log_likelihood(self, hist_2: np.ndarray[float], hist_1: np.ndarray[float], detectors: DetectorRelation) -> float:
        pass

    def alert(self, data):
        binning, is_binning_valid = fetch_field(data, self.in_binning_field)
        if not is_binning_valid:
            return False

        mesh, is_mesh_valid = fetch_field(data, self.in_mesh_field)
        if not is_mesh_valid:
            return False

        log_likelihoods = np.apply_along_axis(self.log_likelihood, 1, mesh['hist_2s'], binning['hist_1'], binning['det_rel'])

        return store_field(data, self.out_field, log_likelihoods)