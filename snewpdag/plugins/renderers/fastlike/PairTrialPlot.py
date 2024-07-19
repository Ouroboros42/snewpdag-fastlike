import logging
import matplotlib.pyplot as plt
import numpy as np

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field

class PairTrialPlot(Node):
    def __init__(self, in_dt_field, filename, in_true_t1_field = None, in_true_t2_field = None, title="Lag Estimator", **kwargs):
        self.in_dt_field = in_dt_field
        self.in_true_t1_field = in_true_t1_field
        self.in_true_t2_field = in_true_t2_field
        self.filename = filename
        self.title=title
        self.count=0
        super().__init__(**kwargs)
    
    def alert(self, data):
        dtinfo, has_info = fetch_field(data, self.in_dt_field)
        if not has_info:
            return False

        true_t1, has_true_t1 = fetch_field(data, self.in_true_t1_field)
        true_t2, has_true_t2 = fetch_field(data, self.in_true_t2_field)

        has_true_dt = has_true_t1 and has_true_t2
        if has_true_dt:
            true_dt = true_t1 - true_t2

        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        fig, ax = plt.subplots()
        ax.set_title(self.title)
        ax.scatter(dtinfo['lag_mesh'], dtinfo['likelihoods'])
        ax.scatter(dtinfo['opt_lags'], dtinfo['opt_likelihoods'])

        if has_true_dt:
            ax.axvline(x=true_dt, color='green', label=f"True dt = {true_dt}")

        ax.axvline(x=dtinfo['dt'], color='blue', label=f"Curve dt = {dtinfo['dt']}")
        ax.axvline(x=dtinfo['opt_dt'], color='orange', label=f"Opt dt = {dtinfo['opt_dt']}")
        ax.legend()
        ax.set_xlabel("Lag / s")
        ax.set_ylabel("Likelihood")

        fig.savefig(filename, dpi=1000, bbox_inches='tight')
        plt.close(fig)

        return True