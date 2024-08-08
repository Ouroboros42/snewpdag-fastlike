import logging
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
import numpy as np

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from itertools import product
from collections import defaultdict

class CompPlot(Node):
    def __init__(self,
        filename, in_summary_field, stat,
        like_methods, est_methods, bin_widths, mesh_spacings,
        title="Pull Summary",
        plot_abs=False,
    **kwargs):
        self.in_summary_field = in_summary_field
        self.filename = filename
        self.stat = stat
        self.like_methods = like_methods
        self.est_methods = est_methods
        self.bin_widths = sorted(bin_widths)
        self.mesh_spacings = sorted(mesh_spacings)
        self.title=title
        self.plot_abs = plot_abs
        super().__init__(**kwargs)
    
    def report(self, data):
        pull_summary, has_info = fetch_field(data, self.in_summary_field)
        if not has_info:
            return False
        
        plots_data = {}
        for key in product(self.like_methods, self.est_methods):
            plots_data[key] = np.empty((len(self.bin_widths), len(self.mesh_spacings)))
            
        min_stat = +float('inf')
        max_stat = -float('inf')

        for case in pull_summary:
            stat = case['results'][self.stat]

            try:
                plots_data[(case['like_method_name'], case['est_method_name'])][self.bin_widths.index(case['bin_width']), self.mesh_spacings.index(case['mesh_spacing'])] = stat
            except (IndexError, KeyError):
                continue

            if self.plot_abs:
                stat = abs(stat)
            min_stat = min(stat, min_stat)
            max_stat = max(stat, max_stat)


        with FileFigure.for_node(self, data, figsize=(20, 20)) as fig:
            grid = ImageGrid(fig, 111,
                nrows_ncols = (len(self.like_methods), len(self.est_methods)),
                share_all = True,
                label_mode = "L",
                cbar_mode = "single",
                axes_pad = 0.1,
            )

            for ax, ((i, like_method), (j, est_method)) in zip(grid, product(enumerate(self.like_methods), enumerate(self.est_methods))):
                if i == 0:
                    ax.set_title(est_method)
                if j == 0:
                    ax.set_ylabel(like_method)                       
                ax.set_xticks(np.arange(len(self.mesh_spacings)), labels=self.mesh_spacings)
                ax.set_yticks(np.arange(len(self.bin_widths)), labels=self.bin_widths)
                
                plot_data = plots_data[(like_method, est_method)]
                if self.plot_abs:
                    img_plot_data = np.abs(plot_data)
                else:
                    img_plot_data = plot_data
                im = ax.imshow(img_plot_data, vmin=min_stat, vmax=max_stat)
                for k, l in product(range(len(self.bin_widths)), range(len(self.mesh_spacings))):
                    val = plot_data[k, l]
                    ax.text(l, k, f"{val:.2g}", ha="center", va="center", color="lightgray")

            ax.cax.colorbar(im)
            ax.cax.toggle_label(True)

        return True