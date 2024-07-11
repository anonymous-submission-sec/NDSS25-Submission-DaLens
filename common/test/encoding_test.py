#! /usr/bin/env python3

import unittest

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

from encoding import *

class TestStringMethods(unittest.TestCase):

  #def test_encode(self):
  #  
  #  self.assertEqual(encode(["1.2.3.4"], "a.b"), "01020304.a.b")
  #  self.assertEqual(encode(["1.2.3.4", "8.8.8.8"], "a.b"), "01020304.08080808.a.b")
  #  self.assertEqual(encode(["1.2.3.4", "8.8.8.8"], ""), "01020304.08080808")
  
  #def test_decode(self):
  #  
  #  self.assertEqual(decode("01020304.a.b", "a.b"), ["1.2.3.4"])
  #  self.assertEqual(decode("01020304.08080808.a.b", "a.b"), ["1.2.3.4", "8.8.8.8"])
  #  self.assertEqual(decode("08080808.01020304.a.b", "a.b"), ["8.8.8.8", "1.2.3.4"])

  #def test_encode_decode(self):
  #  self.assertEqual(decode(encode(["32.45.245.178"])), ["32.45.245.178"])
  #  self.assertEqual(decode(encode(["1.2.3.4"], "a.b"), "a.b"), ["1.2.3.4"])

  #  self.assertEqual(encode(decode("ffffffff.01020304")), "ffffffff.01020304")
  #  self.assertEqual(encode(decode("ffffffff.01020304.a.b", "a.b"), "a.b"), "ffffffff.01020304.a.b")
  def test_enc(self):
    resolvers = {
      "ns0": "1.2.3.4",
      "vp0": "5.6.7.8"
    }
    # Metasymbols, ordering
    self.assertEqual(enc("ns0-vp0", resolvers), "01020304-05060708")
    self.assertEqual(enc("vp0-ns0", resolvers), "05060708-01020304")
    # Literal
    self.assertEqual(enc("ns0-abc", resolvers), "01020304-abc")
    # Suffix
    self.assertEqual(enc("ns0-vp0", resolvers, suffix="xyz"), "01020304-05060708.xyz")
    self.assertEqual(enc("ns0-abc", resolvers, suffix="test"), "01020304-abc.test")



  def test_hex_to_ip(self):
    self.assertEqual(hex_to_ip("ffffffff"), "255.255.255.255")
    self.assertEqual(hex_to_ip("01020304"), "1.2.3.4")
    self.assertEqual(hex_to_ip("0a0b0c0d"), "10.11.12.13")

  def test_ip_to_hex(self):
    pass

  def test_is_hex_ip(self):
    
    self.assertTrue(is_hex_ip("00000000"))
    self.assertTrue(is_hex_ip("ffffffff"))
    self.assertTrue(is_hex_ip("abf432a7"))
      
    self.assertFalse(is_hex_ip("53.188.34.254"))
    self.assertFalse(is_hex_ip("fffffffg"))
    self.assertFalse(is_hex_ip("abc"))
    
  def test_is_ip(self):
    
    self.assertTrue(is_ip("0.0.0.0"))
    self.assertTrue(is_ip("255.255.255.255"))
    self.assertTrue(is_ip("53.188.34.254"))
    
    self.assertFalse(is_ip("53.500.34.256"))
    self.assertFalse(is_ip("a.b.c.d"))
    self.assertFalse(is_ip("1.2.3.4.5"))


    #def test_isupper(self):
    #    self.assertTrue('FOO'.isupper())
    #    self.assertFalse('Foo'.isupper())

    #def test_split(self):
    #    s = 'hello world'
    #    self.assertEqual(s.split(), ['hello', 'world'])
    #    # check that s.split fails when the separator is not a string
    #    with self.assertRaises(TypeError):
    #        s.split(2)

if __name__ == '__main__':
  unittest.main()