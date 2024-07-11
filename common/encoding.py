#! /usr/bin/env python3

import sys

def is_ip(ip):
  octets = ip.strip().split(".")
  if len(octets) != 4:
    return False
  for o in octets:
    if not o.isdigit() or int(o) < 0 or int(o) > 255:
      return False
  return True

def is_hex_ip(h):
  if len(h) != 8:
    return False
  try:
    _ = int(h, 16)
  except ValueError: 
    return False
  return True

def ip_to_hex(ip):
  assert(is_ip(ip))
  octets = ip.strip().split(".")
  hex_octets = [f"{int(o):02x}" for o in octets]
  return "".join(hex_octets)

def hex_to_ip(h):
  assert(is_hex_ip(h))
  octets = [str(int(h[2*i:2*i+2], 16)) for i in range(4)]
  return ".".join(octets)


def enc(encoding, resolver_set, suffix = ""):
  encoded_elems = list()
  for elem in encoding.split('-'):
    try:
      ip = resolver_set[elem]
      encoded_elems.append(ip_to_hex(ip))
    except KeyError:
      print(f"Warning: metasymbol '{elem}' not found. Using it as literal")
      encoded_elems.append(elem)
  name = "-".join(encoded_elems)
  
  if suffix == "":
    return name
  else:
    return name + "." + suffix


def dec(domain):
  # TODO: extend to handle suffix
  # TODO: write test cases
  elem = domain.split('-')
  res = list()
  for e in elem:
    if is_hex_ip(e):
      res.append(hex_to_ip(e))
    else:
      res.append(e)
  return res

""" 
Extract IP addresses from domain name containing encoded IPs.
It starts from the third last label and iterates backwards until it finds a label containing encoded IPs,
i.e. we assume no encoding is in TLD or SLD.
Args:
  domain_name: str, domain name containing encoded IPs
  order: tuple, order of encoded IPs, default is ('ns','vp'), must contain only one 'vp', the rest 'ns'
Returns:
  dict {'ns': list, 'vp': str} or None if domain name does not contain encoded IPs
"""
def extract_id(domain_name:str, order:tuple=('ns','vp')):
  
  labels = domain_name.split('.')  # Separate labels
  
  # Check if domain is long enough
  if len(labels) < 3: # More than TLD and SLD is required
    return None

  # Check all possible positions
  for p in range(len(labels) - 2, -1, -1): # Iterate backwards from third last to first label
    
    if len(labels[p].split('-')) == len(order):       # Check if it contains encoding
      # If so, decode and add fields
      ips = dec(labels[p])
      return {
        'ns': [ips[i] for i in range(len(order)) if i != order.index('vp')],
        'vp': ips[order.index('vp')]
      } 
  # If no encoding found, return None
  return None
