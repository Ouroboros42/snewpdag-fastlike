import logging
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
import numpy as np

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field, store_dict_field

from itertools import product
from collections import defaultdict

from .util import *



class CompPlot(Node):
    """Compares final pull-scores (or other important numerical results) for different methods."""
    
    plot_funcs = {
        None: lambda x: x,
        'abs': np.abs,
        'log': np.log,
        'abslog': lambda x: np.abs(np.log(x)),
        'logabs': lambda x: np.log(np.abs(x)),
    }
    
    def __init__(self,
        filename, in_summary_field, stat,
        like_methods, est_methods, bin_widths, mesh_spacings,
        title="Pull Summary",
        plot_func=None,
        method_label_size = 15,
        big_ax_label_size = 17,
        title_size = 20,
        cmap = "RdYlGn_r",
        num_text_colour = "black",
    **kwargs):
        """
        plot_func specifies how results should be coloured (applied to values before being put in the color-map):
            'abs' - 0 is target, magnitude of values is comparable
            'log' - 0 is target, magnitude varies, values are positive
            'logabs' - 0 is target, magnitude varies
            'abslog' - 1 is target, magnitude varies
        in_summary_field labels a field with the outputs of PairPullPlot
        stat specifies which of the summary stats to plot
        """

        self.in_summary_field = in_summary_field
        self.filename = filename
        self.stat = stat
        self.like_methods = like_methods
        self.est_methods = est_methods
        self.bin_widths = sorted(bin_widths)
        self.mesh_spacings = sorted(mesh_spacings)
        self.title=title
        self.title_size=title_size
        self.plot_func = self.plot_funcs[plot_func]
        self.method_label_size = method_label_size
        self.big_ax_label_size = big_ax_label_size
        self.cmap = cmap
        self.num_text_colour = num_text_colour
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
            plot_stat = self.plot_func(stat)
            min_stat = min(plot_stat, min_stat)
            max_stat = max(plot_stat, max_stat)

        with FileFigure.for_node(self, data, figsize=(20, 18)) as fig:
            grid = ImageGrid(fig, 111,
                nrows_ncols = (len(self.like_methods), len(self.est_methods)),
                share_all = True,
                label_mode = "L",
                cbar_mode = None,
                axes_pad = 0.1,
                cbar_pad = 1.0,
            )

            for ax, ((i, like_method), (j, est_method)) in zip(grid, product(enumerate(self.like_methods), enumerate(self.est_methods))):
                method_label_kwargs = {
                    "transform" : ax.transAxes,
                    "fontsize" : self.method_label_size
                }
                if i == 0:
                    top_text(ax, est_method, **method_label_kwargs)
                if j == len(self.est_methods) - 1:
                    right_text(ax, like_method, **method_label_kwargs)

                ax.set_xticks(np.arange(len(self.mesh_spacings)), labels=self.mesh_spacings)
                ax.set_yticks(np.arange(len(self.bin_widths)), labels=self.bin_widths)
                
                plot_data = plots_data[(like_method, est_method)]
                
                img_plot_data = self.plot_func(plot_data)
                im = ax.imshow(img_plot_data, cmap=self.cmap, vmin=min_stat, vmax=max_stat)
                for k, l in product(range(len(self.bin_widths)), range(len(self.mesh_spacings))):
                    val = plot_data[k, l]
                    ax.text(l, k, f"{val:.2g}", ha="center", va="center", color=self.num_text_colour)
            
            big_ax_label_kwargs = { 
                "transform" : image_grid_trans(fig, grid),
                "fontsize" : self.big_ax_label_size
            }

            top_text(fig, "Estimator Method\n", **big_ax_label_kwargs)
            right_text(fig, "Likelihood Formula\n", **big_ax_label_kwargs)
            left_text(fig, "Bin Width / s\n\n", **big_ax_label_kwargs)
            bottom_text(fig, "\nMesh Spacing / s", **big_ax_label_kwargs)

            top_text(fig, f"{self.title}\n\n", fontsize=self.title_size, transform=big_ax_label_kwargs["transform"])
        return True