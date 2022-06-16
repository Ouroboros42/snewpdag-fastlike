"""
Unit tests for dag library methods
"""
import unittest
from snewpdag.dag.lib import *

class TestLib(unittest.TestCase):

  def test_convert(self):
    t = time_tuple(3.5)
    self.assertEqual(t[0], 3)
    self.assertEqual(t[1], 500000000)

  def test_single(self):
    g = 1000000000
    ti = (5, 40)
    to = normalize_time(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], 40)
    ti = (5, -40)
    to = normalize_time(ti)
    self.assertEqual(to[0], 4)
    self.assertEqual(to[1], g-40)
    ti = (-5, 40)
    to = normalize_time(ti)
    self.assertEqual(to[0], -5)
    self.assertEqual(to[1], 40)
    ti = (-5, -40)
    to = normalize_time(ti)
    self.assertEqual(to[0], -6)
    self.assertEqual(to[1], g-40)
    ti = (5, g+40)
    to = normalize_time(ti)
    self.assertEqual(to[0], 6)
    self.assertEqual(to[1], 40)
    ti = (5, g-40)
    to = normalize_time(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], g-40)
    ti = (5, 0)
    to = normalize_time(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], 0)
    ti = (5, g)
    to = normalize_time(ti)
    self.assertEqual(to[0], 6)
    self.assertEqual(to[1], 0)
    ti = (-5, 0)
    to = normalize_time(ti)
    self.assertEqual(to[0], -5)
    self.assertEqual(to[1], 0)
    ti = (-5, g)
    to = normalize_time(ti)
    self.assertEqual(to[0], -4)
    self.assertEqual(to[1], 0)
    ti = (-5, -g)
    to = normalize_time(ti)
    self.assertEqual(to[0], -6)
    self.assertEqual(to[1], 0)

  def test_multi(self):
    g = 1000000000
    ti = [ (5, 40), (5, -40), (-5, 40), (-5, -40), (5, g+40), (5, g-40) ]
    to = normalize_time(ti)
    self.assertEqual(to[0,0], 5)
    self.assertEqual(to[1,0], 4)
    self.assertEqual(to[2,0], -5)
    self.assertEqual(to[3,0], -6)
    self.assertEqual(to[4,0], 6)
    self.assertEqual(to[5,0], 5)
    self.assertEqual(to[0,1], 40)
    self.assertEqual(to[1,1], g-40)
    self.assertEqual(to[2,1], 40)
    self.assertEqual(to[3,1], g-40)
    self.assertEqual(to[4,1], 40)
    self.assertEqual(to[5,1], g-40)

  def test_norm_dt(self):
    g = 1000000000
    ti = (5, 40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], 40)
    ti = (5, -40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 4)
    self.assertEqual(to[1], g-40)
    ti = (-5, 40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], -4)
    self.assertEqual(to[1], -g+40)
    ti = (-5, -40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], -5)
    self.assertEqual(to[1], -40)
    ti = (5, g+40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 6)
    self.assertEqual(to[1], 40)
    ti = (5, g-40)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], g-40)
    ti = (5, 0)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 5)
    self.assertEqual(to[1], 0)
    ti = (5, g)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], 6)
    self.assertEqual(to[1], 0)
    ti = (-5, 0)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], -5)
    self.assertEqual(to[1], 0)
    ti = (-5, g)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], -4)
    self.assertEqual(to[1], 0)
    ti = (-5, -g)
    to = normalize_time_difference(ti)
    self.assertEqual(to[0], -6)
    self.assertEqual(to[1], 0)

  def test_subtract(self):
    g = 1000000000
    a = (5, 40)
    b = (5, 30)
    c = subtract_time(a, b)
    self.assertEqual(c[0], 0)
    self.assertEqual(c[1], 10)
    c = subtract_time(b, a)
    self.assertEqual(c[0], 0)
    self.assertEqual(c[1], -10)

