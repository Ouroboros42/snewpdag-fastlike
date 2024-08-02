import logging
import numpy as np
from math import floor

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

class SeriesBinningMesh(Node):
    def __init__(self,
        in_field, out_field,
        mesh_spacing: float,
    **kwargs):
        self.in_field = in_field
        self.out_field = out_field

        self.mesh_spacing = mesh_spacing

        super().__init__(**kwargs)

    def alert(self, data):
        binning, is_valid = fetch_field(data, self.in_field)
        if not is_valid:
            return False

        max_lag = binning['max_lag']
        lag_mesh = np.arange(-max_lag, max_lag, self.mesh_spacing)

        return store_dict_field(data, self.out_field,
            lag_mesh=lag_mesh,
            hist_2s = binning['get_hist_2'](lag_mesh),
        )