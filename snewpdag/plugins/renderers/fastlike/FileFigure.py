import matplotlib.pyplot as plt

class FileFigure:
    def __init__(self, filename, dpi=500):
        self.filename = filename
        self.dpi=dpi

    def __enter__(self):
        self.figure = plt.figure()
        return self.figure

    def __exit__(self, *args):
        self.figure.savefig(self.filename, dpi=self.dpi, bbox_inches='tight')
        plt.close(self.figure)