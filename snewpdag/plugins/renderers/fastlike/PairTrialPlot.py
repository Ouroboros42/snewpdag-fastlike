import logging
import matplotlib.pyplot as plt
import numpy as np

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field

class PairTrialPlot(Node):
    def __init__(self,
        filename, in_dt_field,
        in_true_t1_field = None, in_true_t2_field = None,
        title="Lag Estimator",
        colours = [ "coral", "slateblue", "fuchsia", "turquoise", "goldenrod" ],
        sig_fig = 5,
    **kwargs):
        self.in_dt_field = in_dt_field
        self.in_true_t1_field = in_true_t1_field
        self.in_true_t2_field = in_true_t2_field
        self.filename = filename
        self.title=title
        self.colours=colours
        self.sig_fig=sig_fig
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

        for (method, results), colour in zip(dtinfo.items(), self.colours):
            if 'mesh' in results:
                mesh = results['mesh']
                ax.scatter(mesh['lags'], mesh['log_likelihoods'], color=colour)

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

                ax.axvline(x=dt, label=f"{method} dt = ${dt_str}$", color=colour)
                ax.axvspan(xmin=dt-dt_err_neg, xmax=dt+dt_err_pos, alpha=0.1, color=colour)

        if has_true_dt:
            ax.axvline(x=true_dt, color='green', label=f"True dt = ${true_dt:.{self.sig_fig}g}$")

        ax.legend()
        ax.set_xlabel("Lag / s")
        ax.set_ylabel("Likelihood")

        fig.savefig(filename, dpi=1000, bbox_inches='tight')
        plt.close(fig)

        return True