import logging
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as npma
from scipy.stats import norm

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field, store_dict_field, append_tuple_field

class PairPullPlot(Node):
    def __init__(self,
        filename, in_pull_field, title="Pull Distribution",
        stats_summary_array_field = None, stats_summary_labels = {},
    **kwargs):
        self.in_pull_field = in_pull_field
        self.stats_summary_array_field = stats_summary_array_field
        self.stats_summary_labels = stats_summary_labels
        self.filename = filename
        self.title=title
        self.count=0
        super().__init__(**kwargs)

    def valid_hist_value(self, x):
        mask = np.abs(x) <= 1e15
        n_rejected = np.count_nonzero(np.logical_not(mask))
        if n_rejected:
            logging.warning(f"Not displaying {n_rejected} extremely large pull scores in {self.name}")
        return mask
    
    def report(self, data):
        pullinfo, has_info = fetch_field(data, self.in_pull_field)
        if not has_info:
            return False

        raw_scores = pullinfo['series']

        scores = raw_scores[np.isfinite(raw_scores)]
        n_dropped_scores = len(raw_scores) - len(scores)
        if n_dropped_scores:
            logging.warning(f"{n_dropped_scores} infinite pull scores rejected in {self.name}")

        mean = np.mean(scores)
        std = np.std(scores)
        rms_err = np.sqrt(mean ** 2 + std ** 2)

        if self.stats_summary_array_field is not None:
            append_tuple_field(data, self.stats_summary_array_field, {
                **self.stats_summary_labels,
                "results": { "mean": mean, "stdev": std, "rms_err": rms_err }
            })            

        fit = norm(mean.astype(np.float64), std.astype(np.float64))

        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        with FileFigure(filename) as fig:
            ax = fig.subplots()
            ax.set_title(self.title)
            counts, bins, _ = ax.hist(scores[self.valid_hist_value(scores)], density=True, label="Pull Scores")    
            plot_x = np.linspace(np.min(bins), np.max(bins), len(bins) * 10, dtype=np.float64)

            if len(scores) > 1:
                fit = norm(mean.astype(np.float64), std.astype(np.float64))
                fit_y = fit.pdf(plot_x)
                ax.plot(plot_x, fit_y, label=f"Normal fit, mean={mean:.4f}, std={std:.4f}")
            else:
                logging.warning(f"Not enough finite pull scores to calculate stddev for {self.name}")

            ax.set_xlabel("Score")
            ax.set_ylabel("Frequency")
            ax.legend()
                
        return True