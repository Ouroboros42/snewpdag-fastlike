"""
PickleOutput
Configuration options:
  filename:  output filename, with fields
             {0} renderer name
             {1} count index, starting from 0
             {2} burst_id from update data (default 0 if no such field)
"""
import logging
import pickle

from snewpdag.dag import Node
from snewpdag.dag.lib import fill_filename

class PickleOutput(Node):
  def __init__(self, filename, on=['alert', 'report'], **kwargs):
    self.filename = filename
    self.count = 0
    self.on = on
    super().__init__(**kwargs)

  def write_pickle(self, data):
    fname = fill_filename(self.filename, self.name, self.count, data)
    if fname == None:
      logging.error('{}: error interpreting {}', self.name, self.filename)
      return False
    with open(fname, 'wb') as f:
      pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    self.count += 1
    return True

  def alert(self, data):
    return self.write_pickle(data) if 'alert' in self.on else True

  def revoke(self, data):
    return self.write_pickle(data) if 'revoke' in self.on else True

  def reset(self, data):
    return self.write_pickle(data) if 'reset' in self.on else True

  def report(self, data):
    return self.write_pickle(data) if 'report' in self.on else True


