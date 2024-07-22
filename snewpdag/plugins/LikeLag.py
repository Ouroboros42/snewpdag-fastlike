"""
LikeLag - estimate burst time from maximum-likelihood of Poisson distributions  

Arguments:
    tnbins: number of bins to count time series into
    twidth: total period to bin time series over
    nlags: number of possible lags to evaluate
    in_series1_field
    in_series2_field
    out_field:  output field, will receive a dictionary with (at least) fields:
        dt: most likely time difference
        lag_mesh: all lags for which likelihood has been evaluated
        
    det1_bg, det2_bg; expected background rates per unit time for each detector
Optional, keyword-only:
    rel_accuracy = Acceptable proportional err in each likelihood, relative to 1 being 100% error 
    max_lag = maximum possible (absolute) lag
    lead_time = start of event sampling relative to start of series, negative means start before series. Lag range is separately included, so lead_time = 0 is acceptable
    out_key = the key in out_field to assign output to. Defaults to a tuple of the two detector names
    true_t1_field, true_t2_field = fields storing true times if known
"""
import logging
import numpy as np
import scipy.optimize as opt

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, fetch_dict_copy
from snewpdag.values import TimeSeries

from burstlag import DetectorRelation, FactorialCache, likelihood_mesh, find_peak, log_likelihood

from typing import Optional, Callable

class LikeLag(Node):
    def __init__(self, tnbins: int, twidth: float, nlags: int, in_series1_field, in_series2_field, out_field, det1_bg, det2_bg, **kwargs):
        self.tnbins = tnbins
        self.twidth = twidth
        self.nlags = nlags
        self.in_series1_field = in_series1_field
        self.in_series2_field = in_series2_field
        self.out_field = out_field
        self.det1_bg = det1_bg
        self.det2_bg = det2_bg
        self.rel_accuracy = kwargs.pop('rel_accuracy', 1e-2)
        self.max_lag = kwargs.pop('max_lag', 0.1)
        self.lead_time = kwargs.pop('lead_time', 0.0)
        self.out_key = kwargs.pop('out_key', ('Unknown1', 'Unknown2'))

        super().__init__(**kwargs)

    @property
    def tbin_width(self) -> float:
        return self.twidth / self.tnbins

    def get_time_bound(self, compare: Callable[[float, float], float], preset_bound_1: Optional[float], preset_bound_2: Optional[float], first_1: float, first_2: float) -> float:
        if preset_bound_1 is None and preset_bound_2 is None:
            return compare(first_1, first_2)
        elif preset_bound_1 is None:
            return preset_bound_2
        elif preset_bound_2 is None:
            return preset_bound_1
        
        return compare(preset_bound_1, preset_bound_2)

    def get_period(self, time_series_1: TimeSeries, time_series_2: TimeSeries):
        # TODO Adjust for desired behaviour
        return self.get_time_bound(max,
            time_series_1.start, time_series_2.start,
            np.min(time_series_1.times),  np.min(time_series_2.times)
        ), self.get_time_bound(min,
            time_series_1.stop, time_series_2.stop,
            np.max(time_series_1.times),  np.max(time_series_2.times)
        )
    
    def build_hists(self, data: dict):
        time_series_1, series_1_valid = fetch_field(data, self.in_series1_field) 
        if not series_1_valid:
            return False

        time_series_2, series_2_valid = fetch_field(data, self.in_series2_field)
        if not series_2_valid:
            return False

        series_start, series_stop = self.get_period(time_series_1, time_series_2)

        n_events_1 = time_series_1.integral(series_start, series_stop)
        n_events_2 = time_series_2.integral(series_start, series_stop)

        detectors = DetectorRelation.from_counts(self.det1_bg, self.det2_bg, int(n_events_1), int(n_events_2), series_stop - series_start, self.tbin_width)

        hist_start_1 = series_start + self.lead_time + self.max_lag
        hist_stop_1 = hist_start_1 + self.twidth

        histogram_overflow = hist_stop_1 + self.max_lag - series_stop
        if histogram_overflow > 0:
            logging.warning(f"Likelihood histogram exceeds data range by {histogram_overflow}s")

        hist_1, edges_1 = time_series_1.histogram(self.tnbins, hist_start_1, hist_stop_1)

        def get_hist_2(lag: float):
            return time_series_2.histogram(self.tnbins, hist_start_1 - lag, hist_stop_1 - lag)[0]

        # t1_grid, t2_grid = np.meshgrid(time_series_1.times,  time_series_2.times)
        # t_diffs = np.abs(t1_grid - t2_grid)
        # print(np.mean(t_diffs), np.min(t_diffs))

        return detectors, hist_1, get_hist_2, {
            "binning_zero_lag": { "edges": edges_1, "hists": (hist_1, get_hist_2(0)) },
            "t1": first_event_after(time_series_1, series_start),
            "t2": first_event_after(time_series_2, series_start),
        }

    def alert(self, data: dict):
        detectors, hist_1, get_hist_2, extra_info = self.build_hists(data)

        lags, log_likelihoods = likelihood_mesh(detectors, self.rel_accuracy, hist_1, get_hist_2, self.nlags, self.max_lag)

        peak_lag, lag_uncertainty, poly_fit = find_peak(lags, log_likelihoods)

        cache = FactorialCache()

        def neg_lag_like(lag):
            return -log_likelihood(cache, detectors, hist_1, get_hist_2(lag.item()), self.rel_accuracy)

        optimizer_lags = []
        optimizer_likelihoods = []

        def callback(x, negL, _):
            optimizer_lags.append(x.item())
            optimizer_likelihoods.append(-negL)

        res = opt.dual_annealing(neg_lag_like, ((-self.max_lag, self.max_lag),),
            initial_temp=50000,
            callback=callback
        )
        opt_peak = res.x.item()

        out_dict = fetch_dict_copy(data, self.out_field)

        result_dict = {
            "dt": peak_lag,
            "dt_err": lag_uncertainty,
            "var": lag_uncertainty ** 2,
            "bias": 0.0,
            "lag_mesh": lags,
            "likelihoods": log_likelihoods,
            "opt_dt": opt_peak,
            "opt_lags": optimizer_lags,
            "opt_likelihoods": optimizer_likelihoods,
            **extra_info
        }

        out_dict[self.out_key] = result_dict

        store_field(data, self.out_field, out_dict)
        
        return True

def first_event_after(series: TimeSeries, start: float):
    events = series.times
    return np.min(events[events >= start])