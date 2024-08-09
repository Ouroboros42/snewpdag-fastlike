from matplotlib.transforms import Bbox, BboxTransformTo
import numpy as np

__all__ = [ 'top_text', 'bottom_text', 'left_text', 'right_text', 'image_grid_trans' ]

def image_grid_bbox(fig, grid):
    # Courtesty of https://stackoverflow.com/a/15477723
    all_extents = np.array([a.get_position().extents for a in grid])
    widest_extents = np.empty(4)
    widest_extents[:2] = all_extents[:,:2].min(axis=0)
    widest_extents[2:] = all_extents[:,2:].max(axis=0)
    return Bbox.from_extents(widest_extents)

def image_grid_trans(fig, grid):
    bbox = image_grid_bbox(fig, grid)
    return BboxTransformTo(bbox) + fig.transFigure

def top_text(artist, text, rel_pad = 0.01, **kwargs):
    artist.text(0.5, 1 + rel_pad, text,
        ha = 'center', va = 'bottom',
        rotation = 0,
    **kwargs)

def bottom_text(artist, text, rel_pad = 0.01, **kwargs):
    artist.text(0.5, -rel_pad, text,
        ha = 'center', va = 'top',
        rotation = 0,
    **kwargs)

def left_text(artist, text, rel_pad = 0.01, **kwargs):
    artist.text(-rel_pad, 0.5, text,
        ha = 'right', va = 'center',
        rotation = 90,
    **kwargs)

def right_text(artist, text, rel_pad = 0.01, **kwargs):
    artist.text(1 + rel_pad, 0.5, text,
        ha = 'left', va = 'center',
        rotation = 270,
    **kwargs)