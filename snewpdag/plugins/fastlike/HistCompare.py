import logging
import numpy as np

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation, FactorialCache

class HistCompare(Node):
    fact_cache = FactorialCache()

    def __init__(self,
        in_series1_field, in_series2_field, out_field, 
        det1_bg: float, det2_bg: float,
        bin_width: int, window: float,
        pad_time: float = 0.01,
        rel_precision: float = 1e-3,
        source_suppression: float = 1.,
    **kwargs):
        self.in_series1_field = in_series1_field
        self.in_series2_field = in_series2_field
        self.out_field = out_field

        self.bin_width = bin_width
        self.n_bins = int(window / bin_width)
        self.pad_time = pad_time

        self.rel_precision = rel_precision
        self.source_suppression = source_suppression

        self.det1_bg = det1_bg
        self.det2_bg = det2_bg

        super().__init__(**kwargs)

    @property
    def window(self):
        return self.n_bins * self.bin_width

    def alert(self, data):
        time_series_1, series_1_valid = fetch_field(data, self.in_series1_field) 
        if not series_1_valid:
            return False

        time_series_2, series_2_valid = fetch_field(data, self.in_series2_field)
        if not series_2_valid:
            return False

        series_start = max(time_series_1.data_start, time_series_2.data_start)
        series_stop = min(time_series_1.data_stop, time_series_2.data_stop)

        n_events_1 = int(time_series_1.integral(series_start, series_stop))
        n_events_2 = int(time_series_2.integral(series_start, series_stop))

        detectors = DetectorRelation.from_counts(self.det1_bg, self.det2_bg, n_events_1, n_events_2, series_stop - series_start, self.bin_width, self.source_suppression)

        hist_start_1 = series_start + self.pad_time
        hist_stop_1 = hist_start_1 + self.window

        histogram_overflow = hist_stop_1 + self.pad_time - series_stop
        if histogram_overflow > 0:
            logging.warning(f"Likelihood histogram exceeds data range by {histogram_overflow}s")
    
        hist_1, edges = time_series_1.histogram(self.n_bins, hist_start_1, hist_stop_1)
        
        def get_hist_1(lag: float):
            return time_series_1.histogram(self.n_bins, hist_start_1 - lag, hist_stop_1 - lag)[0]

        def get_hist_2(lag: float):
            return time_series_2.histogram(self.n_bins, hist_start_1 - lag, hist_stop_1 - lag)[0]

        @np.vectorize(otypes=[float], excluded={'dets'})
        def get_log_likelihood(lag: float, dets=detectors):
            return dets.log_likelihood(self.fact_cache, hist_1, get_hist_2(lag), self.rel_precision)

        return store_dict_field(data, self.out_field,
            bin_width = self.bin_width,
            n_bins = self.n_bins,
            original_edges = edges,
            hist_1 = hist_1,
            hist_2 = get_hist_2(0),
            get_hist_1 = get_hist_1,
            get_hist_2 = get_hist_2,
            get_log_likelihood = get_log_likelihood
        )