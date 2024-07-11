#! /usr/bin/env python3

import unittest

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

from lib.zone_utils import *

class TestStringMethods(unittest.TestCase):

  def test_compose_rrs(self):
    # Regular correct fields
    test = {
      "name": "test",
      "ttl": 300,
      "class": "IN",
      "type": "A",
      "ans": "1.2.3.4"
    }
    res = compose_records([test])
    r = [x.strip() for x in res.split(" ") if x != ""]
    self.assertEqual(r, ["test", "300", "IN", "A", "1.2.3.4"])
  
  def test_compose_rrs2(self):
    # Missing optional fields
    test = {
      "name": "test",
      "class": "IN",
      "type": "A",
    }
    res = compose_records([test])
    r = [x.strip() for x in res.split(" ") if x != ""]
    self.assertEqual(r, ["test", str(default_rr['ttl']), "IN", "A", default_rr['ans']])
  
  def test_compose_rrs3(self):
    # Illegal fields
    test = {
      "name": "test",
      "ttl": 0,
      "class": "IN",
      "type": "A",
      "ans": "5.6.7.8",
      "color": "red"
    }
    res = compose_records([test])
    r = [x.strip() for x in res.split(" ") if x != ""]
    self.assertEqual(r, ["test", "0", "IN", "A", "5.6.7.8"])
    
if __name__ == '__main__':
  unittest.main()