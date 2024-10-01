import logging
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as npma
from scipy.stats import norm

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field, store_dict_field, append_tuple_field

class PairCountsPlot(Node):
    def __init__(self,
        filename,
        in_count_1_field, in_count_2_field,
        in_hist_bins_field,
        label_1, label_2,
        title=None,
        max_plots = None,
    **kwargs):
        self.in_count_1_field = in_count_1_field
        self.in_count_2_field = in_count_2_field
        self.in_hist_bins_field = in_hist_bins_field
        self.label_1 = label_1
        self.label_2 = label_2
        self.filename = filename
        self.title=title
        self.max_plots = max_plots
        self.plot_count = 0 # Incremented by FileFigure
        super().__init__(**kwargs)

    def alert(self, data):
        if self.max_plots is not None and self.plot_count >= self.max_plots:
            return True

        counts_1, has_count_1 = fetch_field(data, self.in_count_1_field)
        counts_2, has_count_2 = fetch_field(data, self.in_count_2_field)
        hist_bins, has_bins = fetch_field(data, self.in_hist_bins_field)
        if not (has_count_1 and has_count_2 and has_bins):
            return False

        with FileFigure.for_node(self, data, figsize=(20, 5)) as fig:
            (ax1, ax2) = fig.subplots(1, 2)
            if self.title:
                fig.suptitle(self.title)

            for ax, counts, label in ((ax1, counts_1, self.label_1), (ax2, counts_2, self.label_2)):
                ax.stairs(counts, hist_bins)
                ax.set_title(f"Detected events {label}")
                ax.set_xlabel("Time / s")
                ax.set_ylabel("Bin Count")

        return True