"""
RandomParameter

Write a randomly generated value to the payload on alerts, according to a preset distribution

Arguments:
    out_field: field to write random values to on alerts
    dist_spec: Dict of specification for parameter generation, of one of the following types:
        { "type": "uniform", "low": <float> (default 0.0), "high": <float> (default 1.0), "size": <int/tuple[int]> (default None -> scalar) }
        { "type": "normal", "loc": <float> (default 0.0), "scale": <float> (default 1.0), "size": <int/tuple[int]> (default None -> scalar) }
        ...
"""

import logging
import numpy as np
from numpy import random

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field


RANDOM_GENERATORS = {
    "uniform": random.uniform,
    "normal": random.normal
}

class RandomParameter(Node):
    def __init__(self, out_field, dist_spec, **kwargs):
        self.out_field = out_field
        self.random_generator = RANDOM_GENERATORS[dist_spec.pop("type")]
        self.generator_params = dist_spec

        super().__init__(**kwargs)

    def generate_random(self):
        return self.random_generator(**self.generator_params)

    def alert(self, data):
        return store_field(data, self.out_field, self.generate_random())