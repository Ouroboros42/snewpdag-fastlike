"""
LagPull - calculate pull for lag

Arguments:
  in_obs_field: input field containing observed value
  in_err_field: input field containing error on observed value
  in_true_field: input field containing true value
  in_base_field: optional input field to subtract from true value
  out_field: output field to store (obs - (true - base)) / err
  out_diff_field: if not None, output field to store (obs - (true - base))
  on: list of 'alert', 'report', 'revoke', 'reset'
"""
import logging
from snewpdag.dag import Node
from snewpdag.dag.lib import fetch_field, store_field

class LagPull(Node):
  def __init__(self, out_field, in_obs_field, in_true_field, in_err_field = None,
               in_base_field = None, out_diff_field = None, on = ['alert'], **kwargs):
    self.out_field = out_field
    self.in_obs_field = in_obs_field
    self.in_err_field = in_err_field
    self.in_true_field = in_true_field
    self.in_base_field = in_base_field
    self.out_diff_field = out_diff_field
    self.on = on
    super().__init__(**kwargs)

  def calc(self, data):
    obs, exists = fetch_field(data, self.in_obs_field)
    if not exists:
      return False
    err, exists = fetch_field(data, self.in_err_field)
    if not exists:
      return False
    if err == 0.0:
      return False
    truth, exists = fetch_field(data, self.in_true_field)
    if not exists:
      return False
    if self.in_base_field == None:
      base = 0.0
    else:
      base, exists = fetch_field(data, self.in_base_field)
      if not exists:
        return False
      
    dx = obs - (truth - base)

    if self.out_diff_field is not None:
      store_field(data, self.out_diff_field, dx)

    if isinstance(err, (list, tuple)):
      sig = err[dx > 0]
    else:
      sig = err

    score = dx / abs(sig)

    store_field(data, self.out_field, score)
    
    return data

  def alert(self, data):
    return self.calc(data) if 'alert' in self.on else True

  def revoke(self, data):
    return self.calc(data) if 'revoke' in self.on else True

  def reset(self, data):
    return self.calc(data) if 'reset' in self.on else True

  def report(self, data):
    return self.calc(data) if 'report' in self.on else True

