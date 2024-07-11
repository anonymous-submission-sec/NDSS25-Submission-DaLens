#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import lib.BasicMeasurement as basic

import json
from lib.Database import Database

def agg_clen_cname(basic_measurement, get_fields=False):
  if get_fields:
    return ["cchain_tot", "cchain_avg_tries", "cchain_chainlength", "status"]
  return {
    "cchain_tot": basic_measurement.clen_cname_total(),
    "cchain_avg_tries": "{:.2f}".format(basic_measurement.clen_cname_mean_tries()),
    "cchain_chainlength": basic_measurement.clen_cname_chainlength(),
    "status": basic_measurement.get_status_codes()[0]
  }


if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "chain_cname3"

  # Data Source
  db = Database(f"{dataset_dir}/combined/")
  #data_source = f"{dataset_dir}/combined/{measurement}/data"

  # Data Dest
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"
  
  
  data = []

  LIMIT = 4000
  num_loaded = 0
  # Walk database directory 
  for fn in db.traverse_files(prefix=measurement):
    if num_loaded >= LIMIT:
      break

    with open(fn, 'r') as f: # open nameserver file

      # Read, parse, filter data 
      sample = [basic.BasicMeasurement(json.loads(l)) for l in f if l != "\n"]
      #sample = [d for d in sample if d.num_logentries()]
      for i, s in enumerate(sample, 1):
        #queries = [l['query'] for l in s.get_logentries() if l['query'].startswith("n")]
        if not s.cs_clen_cname():
          continue
        if not s.check_status_any('NOERROR'):
          continue
       # if not s.clen_cname_uses_wildcard():
        #if not s.check_status_any("NOERROR"):
       #   continue
        print(f"\nNEW SAMPLE: {fn} line {i}")
        s._clen_cname_debug()
        #print(f"Total: {s.clen_cname_total()}")
        #print(f"Mean tries: {s.clen_cname_mean_tries()}")
        #print(f"Chainlength: {s.clen_cname_chainlength()}")
        #print(f"Wildcard: {s.clen_cname_uses_wildcard()}")
        #print(f"Fine Granularity: {s.clen_cname_fine_subquery_granularity()}")
      
      data += sample
      num_loaded += len(sample)





