import logging
import numpy as np
from math import floor

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from burstlag import DetectorRelation

class SeriesBinning(Node):
    def __init__(self,
        in_series1_field, in_series2_field, out_field, 
        det1_bg: float, det2_bg: float,
        window: float, bin_width: float,
        max_lag: float = 0.1,
        source_suppression: float = 1.,
    **kwargs):
        self.in_series1_field = in_series1_field
        self.in_series2_field = in_series2_field
        self.out_field = out_field

        self.window = window
        self.bin_width = bin_width

        self.max_lag = max_lag

        self.source_suppression = source_suppression

        self.det1_bg = det1_bg
        self.det2_bg = det2_bg

        super().__init__(**kwargs)
    
    @property
    def n_bins(self) -> int:
        return floor(self.window / self.bin_width)

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

        hist_start_1 = max(time_series_1.data_start, time_series_2.data_start + self.max_lag)
        hist_stop_1 = hist_start_1 + self.window

        histogram_overflow = hist_stop_1 - min(time_series_1.data_stop, time_series_2.data_stop - self.max_lag)
        if histogram_overflow > 0:
            logging.warning(f"Event time histogram exceeds data range by {histogram_overflow}s")

        det_rel = DetectorRelation.from_counts(
            self.det1_bg, self.det2_bg,
            n_events_1, n_events_2,
            series_stop - series_start,
            self.bin_width,
            self.source_suppression
        )

        def bin_hist(series, lag: float = 0.0):
            return series.histogram(self.n_bins, hist_start_1 - lag, hist_stop_1 - lag)[0]

        hist_1 = bin_hist(time_series_1)

        @np.vectorize(signature='()->(n)')
        def get_hist_2(lag: float = 0.0):
            return bin_hist(time_series_2, lag)

        return store_dict_field(data, self.out_field,
            max_lag = self.max_lag,
            window = self.window,
            det_rel = det_rel,
            hist_1 = hist_1,
            get_hist_2 = get_hist_2
        )