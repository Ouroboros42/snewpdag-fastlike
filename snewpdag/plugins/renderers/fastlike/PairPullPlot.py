import logging
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as npma
from scipy.stats import norm

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field, store_dict_field

class PairPullPlot(Node):
    def __init__(self, filename, in_pull_field, out_stats_field = None, title="Pull Distribution", **kwargs):
        self.in_pull_field = in_pull_field
        self.out_stats_field = out_stats_field
        self.filename = filename
        self.title=title
        self.count=0
        super().__init__(**kwargs)
    
    def report(self, data):
        pullinfo, has_info = fetch_field(data, self.in_pull_field)
        if not has_info:
            return False

        scores = npma.masked_invalid(pullinfo['series'])
            
        mean = np.mean(scores)
        std = np.std(scores)
        rms_err = np.sqrt(mean ** 2 + std ** 2)

        if self.out_stats_field is not None:
            store_dict_field(data, self.out_stats_field, mean=mean, stdev=std, rms_err=rms_err)            

        fit = norm(mean.astype(np.float64), std.astype(np.float64))

        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        with FileFigure(filename) as fig:
            ax = fig.subplots()
            ax.set_title(self.title)
            counts, bins, _ = ax.hist(scores, density=True, label="Pull Scores")
            plot_x = np.linspace(np.min(bins), np.max(bins), len(bins) * 10, dtype=np.float64)
            fit_y = fit.pdf(plot_x)
            ax.plot(plot_x, fit_y, label=f"Normal fit, mean={mean:.4f}, std={std:.4f}")
            ax.set_xlabel("Score")
            ax.set_ylabel("Frequency")
            ax.legend()

        return True