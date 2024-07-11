#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import lib.BasicMeasurement as basic

import json
from lib.Database import Database

""" Get dict of unique egress IPs for a resolver for a given list of vantage points"""
def agg_max_fetch(basic_measurement):
  return {
    "rr": basic_measurement.get_resolver(),
    "vp": basic_measurement.get_vantagepoint(),
    "concurrent_fetches": basic_measurement.max_fetch_concurrent(),
    "failover_fetches": basic_measurement.max_fetch_failover(),
  }
def agg_max_fetch2(basic_measurement):
  return {
    "concurrent_fetches": basic_measurement.max_fetch_concurrent(),
    "failover_fetches": basic_measurement.max_fetch_failover(),
  }

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "maxfetch2"

  # Data Source
  db = Database(f"{dataset_dir}/combined/")
  #data_source = f"{dataset_dir}/combined/{measurement}/data"

  # Data Dest
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"


  #db.process_dataset(data_source, out_file, agg_max_fetch, lambda x: x.cs_max_fetch(), zoneconf=zoneconf)
  
  data = []

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
        if not s.cs_max_fetch():
          continue
        s.fetch_on_succ_total(debug=True)
        s.fetch_on_succ_ns_tried(debug=True)
        s.fetch_on_succ_mean_tries(debug=True)
        s.fetch_on_fail_total(debug=True)
        s.fetch_on_fail_ns_tried(debug=True)
        s.fetch_on_fail_mean_tries(debug=True)
        s.fetch_fine_subquery_granularity(debug=True)
        #failover = s.max_fetch_failover(debug=True)
        #s.max_fetch_tries_on_fail(debug=True)
        #s.max_fetch_num_ns_tried(debug=True)
        #concurrent = s.max_fetch_concurrent(debug=True)
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

      data += sample
      num_loaded += len(sample)





