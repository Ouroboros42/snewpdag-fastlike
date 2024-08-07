import logging
import matplotlib.pyplot as plt
import numpy as np

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field

class PairTrialPlot(Node):
    def __init__(self,
        filename,
        in_lag_mesh_field, in_like_mesh_field, in_ests_field,
        in_true_t1_field = None, in_true_t2_field = None,
        max_plots = None,
        title = "Lag Estimator",
        colours = [ "coral", "slateblue", "fuchsia", "turquoise", "goldenrod" ],
        sig_fig = 5,
    **kwargs):
        self.in_ests_field = in_ests_field
        self.in_lag_mesh_field = in_lag_mesh_field
        self.in_like_mesh_field = in_like_mesh_field
        self.in_true_t1_field = in_true_t1_field
        self.in_true_t2_field = in_true_t2_field
        self.filename = filename
        self.title=title
        self.colours=colours
        self.sig_fig=sig_fig
        self.max_plots = max_plots
        self.count=0
        super().__init__(**kwargs)
    
    def alert(self, data):
        if self.max_plots is not None and self.count >= self.max_plots:
            return True

        lag_mesh, lag_mesh_valid = fetch_field(data, self.in_lag_mesh_field)
        if not lag_mesh_valid:
            return False
        like_mesh, like_mesh_valid = fetch_field(data, self.in_like_mesh_field)
        if not like_mesh_valid:
            return False
        estinfo, has_info = fetch_field(data, self.in_ests_field)
        if not has_info:
            return False

        true_t1, has_true_t1 = fetch_field(data, self.in_true_t1_field)
        true_t2, has_true_t2 = fetch_field(data, self.in_true_t2_field)

        has_true_dt = has_true_t1 and has_true_t2
        if has_true_dt:
            true_dt = true_t1 - true_t2

        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        with FileFigure(filename) as fig:
            ax = fig.subplots()
            ax.set_title(self.title)
            ax.scatter(lag_mesh, like_mesh)

            for (method, results), colour in zip(estinfo.items(), self.colours):
                if 'dt' in results:
                    dt = results['dt']
                    dt_str = f"{dt:.{self.sig_fig}g}"
                    if 'dt_err' in results:
                        dt_err = results['dt_err']
                        if isinstance(dt_err, (list, tuple)):
                            dt_err_neg, dt_err_pos = dt_err
                            dt_str += f"\\pm_{{{dt_err_neg:.{self.sig_fig}g}}}^{{{dt_err_pos:.{self.sig_fig}g}}}"
                        else:
                            dt_err_pos = dt_err_neg = dt_err
                            dt_str += f"\\pm{dt_err:.{self.sig_fig}g}"

                        if np.all(np.isfinite([dt_err_neg, dt_err_pos])):
                            ax.axvspan(xmin=dt-dt_err_neg, xmax=dt+dt_err_pos, alpha=0.1, color=colour)

                    ax.axvline(x=dt, label=f"{method} dt = ${dt_str}$", color=colour)

            if has_true_dt:
                ax.axvline(x=true_dt, color='green', label=f"True dt = ${true_dt:.{self.sig_fig}g}$")

            ax.legend()
            ax.set_xlabel("Lag / s")
            ax.set_ylabel("Likelihood")

        return True