"""
DynamicTrueTimes - generate true arrival times from angles in payload

Arguments:
  detector_location: filename of detector database for DetectorDB
  detectors: list of detectors for which to generate burst times
  sn_spec_field: field containing dict with
    direction_vec: 3-element array pointing in supernova direction
    time: sn_time string, e.g., '2021-11-01 05:22:36.328'
  out_field: field to put output
  epoch_base (optional): starting sn_time for epoch, float value or field specifier
    (string or tuple)

Input:
  [epoch_base]: float value of starting sn_time for epoch, in unix epoch

Output:
  [out_field]/true_sn_ra: right ascension (radians)
  [out_field]/true_sn_dec: declination (radians)
  [out_field]/dets/<det_id>/true_t: arrival sn_time, (float) seconds in snewpdag sn_time
"""
import logging
import numbers
import numpy as np
from astropy.time import Time
from astropy import constants as const
from astropy import units as u
from astropy.coordinates import GCRS, ICRS, SkyCoord, CartesianRepresentation, UnitSphericalRepresentation

from snewpdag.dag import Node, DetectorDB
from snewpdag.dag.lib import fetch_field, fetch_dict_copy, store_field

class DynamicTrueTimes(Node):
  def __init__(self, detector_location, detectors, sn_spec_field, out_field="truth", epoch_base=0.0, **kwargs):
    self.detector_db = DetectorDB(detector_location)
    self.sn_spec_field = sn_spec_field
    self.out_field = out_field
    self.epoch_base = epoch_base
    if not isinstance(self.epoch_base, (numbers.Number, str, list, tuple)):
      logging.error(f'TrueTimes.__init__: unrecognized epoch_base {self.epoch_base}. Set to 0.')
      self.epoch_base = 0.0

    self.dets = set(detectors)

    super().__init__(**kwargs)

  @staticmethod
  def normalised(vec: np.ndarray):
    mag = np.linalg.norm(vec)
    if mag == 0.0:
      raise ValueError("Tried to normalise zero vector!")
    return vec / mag

  def alert(self, data):
    out_dict = fetch_dict_copy(data, self.out_field)

    sn_spec, has_spec = fetch_field(data, self.sn_spec_field)
    if not has_spec:
      return False

    sn_direction = self.normalised(np.array(sn_spec['direction_vec']))

    sn_time = Time(sn_spec['time'])
    time_unix = sn_time.to_value('unix', 'long') # float, unix epoch

    sky_coord = SkyCoord(
      x=sn_direction[0], y=sn_direction[1], z=sn_direction[2],
      unit=(u.dimensionless_unscaled,), frame=GCRS, representation_type='cartesian',
      obstime=sn_time
    )
    angular_coords = sky_coord.transform_to(ICRS).represent_as(UnitSphericalRepresentation)
  
    out_dict['true_sn_ra'] = angular_coords.lon.to(u.radian).value
    out_dict['true_sn_dec'] = angular_coords.lat.to(u.radian).value

    if isinstance(self.epoch_base, numbers.Number):
      t0 = self.epoch_base
    elif isinstance(self.epoch_base, (str, list, tuple)):
      t0, is_epoch_valid = fetch_field(data, self.epoch_base)
      if not is_epoch_valid:
        raise KeyError(f"No epoch provided at field {self.epoch_base}")

    time_base = time_unix - t0

    # generate true times for each detector.
    # given sn_time is when wavefront arrives at Earth origin.
    ts = {}
    for dname in self.dets:
      det = self.detector_db.get(dname)
      pos = det.get_xyz(sn_time) # detector in GCRS at given sn_time
      logging.info('pos[{}] = {}'.format(dname, pos))
      logging.info('  sn pos = {}'.format(sn_direction))
      dt = - np.dot(det.get_xyz(sn_time), sn_direction) / const.c # intersect
      t1 = time_base + dt.to(u.s).value
      ts[dname] = {
        'true_t': t1, # s in snewpdag sn_time
      }

    out_dict['dets'] = ts
    store_field(data, self.out_field, out_dict)
    return data

