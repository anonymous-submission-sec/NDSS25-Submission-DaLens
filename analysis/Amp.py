#! /usr/bin/env python3

import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import lib.BasicMeasurement as basic
import lib.plot as plot
import matplotlib.pyplot as plt
from lib.Database import Database
import lib.Aggregate as agg
import json
import csv


if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "fanout-fanout"

  # Data Source
  db = Database(f"{dataset_dir}/combined")
  

  # Output
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"


  
  data = []

  LIMIT = 100
  total = 0
  success = 0
  with_logentries = 0
  # Walk database directory 
  for file in db.traverse_files(prefix=measurement):
    #if total >= LIMIT:
    #  break
    with open(file, 'r') as f: # open nameserver file

      # Read, parse, filter data 
      sample = [basic.BasicMeasurement(json.loads(l)) for l in f if l != "\n"]
      total += len(sample)
      for i, s in enumerate(sample):
        if not s.cs_maf():
          continue
        if not s.maf() > 2000:
          continue
        print(f"\n Sample: nameserver: {s.get_resolver()} line {i}")
        s._maf_debug()
        print(f"MAF: {s.maf()}")
        print(f"MAF Total: {s.maf_total()}")
        print(f"RTT: {s.maf_rtt()}")
        print(f"Entry Delta: {s.maf_entry_delta()}")
