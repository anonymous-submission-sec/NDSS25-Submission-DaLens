#! /usr/bin/env python3

import json
import csv

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import config as c
import common.jsonline as io

def read_enum_output(DISCOVERY_FILE: str) -> list:
  with open(DISCOVERY_FILE, 'r') as f:
    content = f.read().split('\n')
    resolvers = [json.loads(l) for l in content if l != ""]
    return resolvers


def write_resolver_file(data, RESOLVER_FILE: str) -> None:
  with open(RESOLVER_FILE, 'w') as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    for d in data:
      writer.writerow(d)

def has_answer(response: dict) -> bool:
  name = response['dns_questions'][0]['name']
  return any([name == ans['name'] for ans in response['dns_answers']])


if __name__ == "__main__":

  
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("--i", nargs="+", required=True,
    help="Resolver files")
  parser.add_argument("--o", default="intersection.csv", metavar="resolver_file",
    help="Name of the output file used by query patterns")
  
  args = parser.parse_args()
  
  DISCOVERY_FILES = args.i
  RESOLVER_FILE = args.o

  assert RESOLVER_FILE.endswith(".csv"), f"Output file must be a .csv, not '{RESOLVER_FILE}'"

  res = list()
  # Read all resolver files
  for f in DISCOVERY_FILES:
    assert f.endswith(".csv"), f"Input file must be a .csv, not '{f}'"
    resolvers = io.read_csv(f)
    # Extract ns0
    ns_dict = {el['ns0']: el for el in resolvers}
    # Append to list of file dicts
    res.append(ns_dict)
  
  # Find intersection between ns0 sets of all files
  shared_ips = list()
  for r in res:
    shared_ips.append(set(r.keys()))
  shared_ips = list(set(shared_ips[0]).intersection(*shared_ips))

  # Create Aggregate file
  #data = list()
  #for el in res:
  #  data.append({
  #    "ns0": el['saddr'],
  #    "vp0": el["daddr"],
  #    "rcode": el["dns_rcode"],
  #    "app_success": el["app_success"],
  #    #"correct_resolved": has_answer(el),
  #    "ts": el["timestamp_str"],
  #    #"question": el['dns_questions'][0]['name'],

  #  })
#  # Filter successful
#  data = [d for d in data if d['rcode'] == 0]
#  # Filter correct
#  data = [d for d in data if d['correct_resolved']]
  
  # find entire dictionaries for each ns0 in the intersection
  res = [res[0][ns0] for ns0 in shared_ips]

  sortkey = lambda x: tuple([int(y) for y in x['ns0'].split(".")])
  #data = sorted(data, key=lambda x: int(x['ns0'].split(".")[0]))
  data = sorted(res, key=sortkey)
  #data = sorted(res)
  io.write_csv(data, RESOLVER_FILE)
  






