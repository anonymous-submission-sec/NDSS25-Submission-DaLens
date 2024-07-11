#! /usr/bin/env python3

import unittest

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import materialize as m


class TestStringMethods(unittest.TestCase):

  def test_create_queries(self):
    # Tests simplest case
    pattern = {
      "suffix": "ta6.ch",
      "zone": [{"name": "<id>",}],
      "queries": [{ 
          "ns": "ns0",
          "vp": "vp0",
          "query": "ns0-vp0"}]
    }
    resolvers = {
      "vp0": "5.6.7.8",
      "ns0": "1.2.3.4"
    }
    
    res = m.create_queries(pattern, resolvers, "ta6.ch")

    self.assertEqual(len(res['queries']), 1)
    self.assertEqual(res['queries'][0]['ns'], "1.2.3.4")
    self.assertEqual(res['queries'][0]['vp'], "5.6.7.8")
    self.assertEqual(res['queries'][0]['query'], "01020304-05060708.ta6.ch")
  
  def test_create_queries2(self):
    # Tests use of 2 distinct resolvers (ns) resulting in two different domain names
    pattern = {
      "suffix": "ta6.ch",
      "zone": [{"name": "bla"}],
      "queries": [{ 
          "ns": "ns0",
          "vp": "vp0",
          "query": "ns0-vp0",
        },{ 
          "ns": "ns1",
          "vp": "vp0",
          "query": "ns1-vp0",
        }]}
    resolvers = {
      "vp0": "5.6.7.8",
      "ns0": "1.2.3.4",
      "ns1": "1.2.3.5"
    }

    res = m.create_queries(pattern, resolvers, "ta6.ch")
    
    self.assertEqual(len(res['queries']), 2)
    self.assertEqual(res['queries'][0]['ns'], "1.2.3.4")
    self.assertEqual(res['queries'][0]['vp'], "5.6.7.8")
    self.assertEqual(res['queries'][0]['query'], "01020304-05060708.ta6.ch")
    self.assertEqual(res['queries'][1]['ns'], "1.2.3.5")
    self.assertEqual(res['queries'][1]['vp'], "5.6.7.8")
    self.assertEqual(res['queries'][1]['query'], "01020305-05060708.ta6.ch")
  
  def test_create_queries3(self):
    # Tests use of 2 distinct vantage points (vp) resulting in two different domain names
    pattern = {
      "suffix": "ta6.ch",
      "zone": [{"name": "<id>"}],
      "queries": [{ 
          "ns": "ns0",
          "vp": "vp0",
          "query": "ns0-vp0",
        },{ 
          "ns": "ns0",
          "vp": "vp1",
          "query": "ns0-vp1",
        }]}
    resolvers = {
      "vp0": "5.6.7.8",
      "vp1": "5.6.7.9",
      "ns0": "1.2.3.4",
    }
    res = m.create_queries(pattern, resolvers, "ta6.ch")

    self.assertEqual(len(res['queries']), 2)
    self.assertEqual(res['queries'][0]['ns'], "1.2.3.4")
    self.assertEqual(res['queries'][0]['vp'], "5.6.7.8")
    self.assertEqual(res['queries'][0]['query'], "01020304-05060708.ta6.ch")
    self.assertEqual(res['queries'][1]['ns'], "1.2.3.4")
    self.assertEqual(res['queries'][1]['vp'], "5.6.7.9")
    self.assertEqual(res['queries'][1]['query'], "01020304-05060709.ta6.ch")
  
  def test_variable_ttl(self):
    # Tests whether varying TTL in pattern is carried to zone file
    pattern = {
      "zone": [{
        "name": "ns0-vp0",
        "ttl": 13}],
      "queries": [{ 
          "ns": "ns0",
          "vp": "vp0",
          "query": "ns0-vp0",
        }]}
    resolvers = {
      "ns0": "1.2.3.4",
      "vp0": "5.6.7.8"
    }
    res = m.create_queries(pattern, resolvers, "ta6.ch")
    
    self.assertEqual(len(res['queries']), 1)
    self.assertEqual(res['queries'][0]['ns'], "1.2.3.4")
    self.assertEqual(res['queries'][0]['vp'], "5.6.7.8")
    self.assertEqual(res['queries'][0]['query'], "01020304-05060708.ta6.ch")
    
    zone = m.create_zone(pattern, resolvers, "ta6.ch")
    self.assertEqual(len(zone), 1)
    self.assertEqual(int(zone[0]['ttl']), 13)
  
  def test_random_subdomain(self):
    # Tests whether varying TTL in pattern is carried to zone file
    pattern = {
      "suffix": "ta6.ch",
      "zone": [{
        "name": "ns0-vp0",
        "random_subdomains": True}],
      "queries": [{ 
          "ns": "ns0",
          "vp": "vp0",
          "query": "ns0-vp0",
          "repeat": 2,
          "random_subdomains": True
        }]}
    resolvers = {
      "ns0": "1.2.3.4",
      "vp0": "5.6.7.8"
    }
    res = m.create_queries(pattern, resolvers, "ta6.ch")

    # Carry over "random_subdomains" for queries
    self.assertEqual(len(res['queries']), 1)
    self.assertEqual(res['queries'][0]['random_subdomains'], True)
    # Zone without suffix 
    zone = m.create_zone(pattern, resolvers)
    self.assertEqual(len(zone), 1)
    self.assertEqual(zone[0]['name'], "*.01020304-05060708")
    # Zone with suffix 
    zone = m.create_zone(pattern, resolvers, suffix="ta6.ch")
    self.assertEqual(len(zone), 1)
    self.assertEqual(zone[0]['name'], "*.01020304-05060708.ta6.ch.")


    
if __name__ == '__main__':
  unittest.main()

