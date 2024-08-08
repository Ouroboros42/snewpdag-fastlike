import matplotlib.pyplot as plt
from snewpdag.dag.lib import fill_filename

class FileFigure:
    def __init__(self, filename, dpi=200, **kwargs):
        self.filename = filename
        self.dpi=dpi
        self.kwargs = kwargs

    @classmethod
    def for_node(cls, node, data, **kwargs):
        if not hasattr(node, 'plot_count'):
            node.plot_count = 0

        filename = fill_filename(node.filename, node.name, node.plot_count, data)
        node.plot_count += 1
        return cls(filename, **kwargs)

    def __enter__(self):
        self.figure = plt.figure(**self.kwargs)
        return self.figure

    def __exit__(self, *args):
        self.figure.savefig(self.filename, dpi=self.dpi, bbox_inches='tight')
        plt.close(self.figure)