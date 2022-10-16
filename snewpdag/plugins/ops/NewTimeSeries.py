"""
NewTimeSeries - initialize an empty TimeSeries object

Arguments:
  out_field:  output field name
  start (optional):  float to indicate start time
  stop (optional):  float to indicate stop time
"""
import logging
import numpy as np
import numbers

from snewpdag.dag import Node
from snewpdag.values import TimeSeries

class NewTimeSeries(Node):
  def __init__(self, out_field, **kwargs):
    self.out_field = out_field
    self.start = kwargs.pop('start', None)
    self.stop = kwargs.pop('stop', None)
    super().__init__(**kwargs)

  def alert(self, data):
    data[self.out_field] = TimeSeries(self.start, self.stop)
    return data

