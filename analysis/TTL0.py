#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import lib.BasicMeasurement as basic

import json
from lib.Database import Database

def agg_ttl0(basic_measurement, get_fields=False):
  if get_fields:
    return ["ttl0_const", "ttl0_at_client", "ttl0_client_max", "ttl0_server_honors"]
  return {
    "ttl0_const": basic_measurement.ttl_constant_client_ttl(),
    "ttl0_at_client": basic_measurement.ttl_tell_client_zero(),
    "ttl0_client_max": basic_measurement.ttl_max_client_ttl(),
    "ttl0_server_honors": basic_measurement.ttl_server_honors_zero(),
  }

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "ttl0"

  # Data Source
  db = Database(f"{dataset_dir}/combined/")
  #data_source = f"{dataset_dir}/combined/{measurement}/data"

  # Data Dest
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"
  
 # data = []

  LIMIT = 70
  num_loaded = 0
  # Walk database directory 
  for f in db.traverse_files(prefix=measurement):
    if num_loaded >= LIMIT:
      break

    with open(f, 'r') as f: # open nameserver file

      # Read, parse, filter data 
      sample = [basic.BasicMeasurement(json.loads(l)) for l in f if l != "\n"]
      #sample = [d for d in sample if d.num_logentries()]
      for s in sample:
        #queries = [l['query'] for l in s.get_logentries() if l['query'].startswith("n")]
        print("\nNEW SAMPLE:")
        if not s.cs_ttl0():
          continue
        s._ttl_debug()
        print(f"Server honors: {s.ttl_server_honors_zero()}")
        print(f"Constant TTL: {s.ttl_constant_client_ttl()}")
        print(f"Client TTL0: {s.ttl_tell_client_zero()}")
        print(f"Client TTL max: {s.ttl_max_client_ttl()}")
        #print(s.get_status_codes())
        #if concurrent == 0 or failover == 0:
        #  print(f"k is zero:")
        #  s.max_fetch_concurrent(debug=True)
        #  s.max_fetch_failover(debug=True)
        #  print(s.get_status_codes())
        #  print()
        
        #if concurrent > failover:
        #  print(f"Higher concurrent than failover:")
        #  s.max_fetch_concurrent(debug=True)
        #  s.max_fetch_failover(debug=True)
        #  print()

      num_loaded += len(sample)

