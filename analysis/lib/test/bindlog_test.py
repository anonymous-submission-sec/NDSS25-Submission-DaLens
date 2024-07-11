#! /usr/bin/env python3

import unittest

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)


import bindlog

class TestStringMethods(unittest.TestCase):

  def test_parse1(self):
    logline = "11-Jan-2024 15:02:58.419 info: client @0x7f87e01ba8d8 210.94.11.144#44270 (kt3w.01ed0ab1-9de6617e.ta6.ch): query: kt3w.01ed0ab1-9de6617e.ta6.ch IN A -E(0)DCV (207.154.207.150)"

    entry = bindlog.parse(logline, "ta6.ch")
    self.assertEqual(entry['ip'], '210.94.11.144')
    self.assertEqual(entry['query'], 'kt3w.01ed0ab1-9de6617e.ta6.ch')
    self.assertEqual(entry['type'], 'A')
    self.assertEqual(entry['timestamp'], '11-Jan-2024 15:02:58.419')

    entry = bindlog.extract_id2(entry)
    self.assertEqual(entry['ns'], "1.237.10.177")
    self.assertEqual(entry['vp'], "157.230.97.126")

  def test_parse2(self):
    logline = "12-Jan-2024 10:38:21.100 info: client @0x7f5240182ea8 173.194.96.194#35977 (5E82b4E1-D45982B4-8A44602B.tA6.ch): query: 5E82b4E1-D45982B4-8A44602B.tA6.ch IN A -E(0)DC (207.154.207.150) [ECS 2a01:4f8:1c0c:4000::/56/0]"

    entry = bindlog.parse(logline, "ta6.ch")
    self.assertEqual(entry['ip'], '173.194.96.194')
    self.assertEqual(entry['query'], '5e82b4e1-d45982b4-8a44602b.ta6.ch')
    self.assertEqual(entry['type'], 'A')
    self.assertEqual(entry['timestamp'], '12-Jan-2024 10:38:21.100')
  
  def test_parse3(self):
    logline = "12-Jan-2024 10:38:21.100 info: client @0x7f5240182ea8 173.194.96.194#35977 (5E82b4E1-D45982B4-8A44602B.tA6.ch): query: 5E82b4E1-D45982B4-8A44602B.tA6.ch IN A -E(0)DC (207.154.207.150) [ECS 2a01:4f8:1c0c:4000::/56/0]"

    entry = bindlog.parse(logline, "ta7.ch")
    self.assertEqual(entry, None)
    
    logline = "12-Feb-2024 13:53:17.533 queries: info: client @0x7f188816bd68 193.232.132.82#10575 (a4d7482b-92be5bd0.ta6.ch): query: a4d7482b-92be5bd0.ta6.ch IN A -E(0)DC (207.154.207.150)"
    entry = bindlog.parse(logline, "ta6.ch")
    self.assertEqual(entry, None)

  def test_extract1(self):
    logline = "11-Jan-2024 15:02:58.419 info: client @0x7f87e01ba8d8 210.94.11.144#44270 (kt3w.01ed0ab1-9de6617e.ta6.ch): query: kt3w.01ed0ab1-9de6617e.ta6.ch IN A -E(0)DCV (207.154.207.150)"
    
    entry = bindlog.parse(logline, "ta6.ch")
    entry = bindlog.extract_id(entry)
    self.assertEqual(entry['ns'], "1.237.10.177")
    self.assertEqual(entry['vp'], "157.230.97.126")
    
    entry = bindlog.parse(logline, "ta6.ch")
    entry = bindlog.extract_id2(entry, ['ns', 'vp'])
    self.assertEqual(entry['ns'][0], "1.237.10.177")
    self.assertEqual(entry['vp'], "157.230.97.126")
    
    entry = bindlog.parse(logline, "ta6.ch")
    entry = bindlog.extract_id2(entry, ['vp', 'ns'])
    self.assertEqual(entry['vp'], "1.237.10.177")
    self.assertEqual(entry['ns'][0], "157.230.97.126")
  
  def test_extract2(self):
    logline = "12-Jan-2024 10:38:21.100 info: client @0x7f5240182ea8 173.194.96.194#35977 (5E82b4E1-D45982B4-8A44602B.tA6.ch): query: 5E82b4E1-D45982B4-8A44602B.tA6.ch IN A -E(0)DC (207.154.207.150) [ECS 2a01:4f8:1c0c:4000::/56/0]"

    entry = bindlog.parse(logline, "ta6.ch")
    entry = bindlog.extract_id2(entry, ['ns','ns','vp'])
    self.assertEqual(entry['ns'][0], "94.130.180.225")
    self.assertEqual(entry['ns'][1], "212.89.130.180")
    self.assertEqual(entry['vp'], "138.68.96.43")
    
    entry = bindlog.parse(logline, "ta6.ch")
    entry = bindlog.extract_id2(entry, ['ns','vp','ns'])
    self.assertEqual(entry['ns'][0], "94.130.180.225")
    self.assertEqual(entry['vp'], "212.89.130.180")
    self.assertEqual(entry['ns'][1], "138.68.96.43")
    

if __name__ == '__main__':
  unittest.main()