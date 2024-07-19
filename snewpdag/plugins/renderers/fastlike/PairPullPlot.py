import logging
import matplotlib.pyplot as plt
import numpy as np

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename, fetch_field, store_field

class PairPullPlot(Node):
    def __init__(self, in_pull_field, filename, title="Pull Distribution", **kwargs):
        self.in_pull_field = in_pull_field
        self.filename = filename
        self.title=title
        self.count=0
        super().__init__(**kwargs)
    
    def report(self, data):
        pullinfo, has_info = fetch_field(data, self.in_pull_field)
        if not has_info:
            return False
            
        filename = fill_filename(self.filename, self.name, self.count, data)
        self.count += 1

        fig, ax = plt.subplots()
        ax.set_title(self.title)
        ax.hist(pullinfo['series'], density=True)
        ax.set_xlabel("Pull Score")
        ax.set_ylabel("Frequency")

        fig.savefig(filename, dpi=1000, bbox_inches='tight')
        plt.close(fig)

        return True