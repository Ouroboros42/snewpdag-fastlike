import logging
import matplotlib.pyplot as plt
import numpy as np

from .FileFigure import FileFigure

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field, store_dict_field

class MetaPullPlot(Node):
    def __init__(self, filename, in_field, title="Pull Distribution", **kwargs):
        self.in_field = in_field
        self.filename = filename
        self.title=title
        self.count=0
        super().__init__(**kwargs)
    
    def report(self, data):
        pullinfo, has_info = fetch_field(data, self.in_field)
        if not has_info:
            return False

        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        with FileFigure(filename) as fig:
            ax = fig.subplots()
            for bin_width, bininfo in pullinfo.items():
                

                ax.plot()


        return True