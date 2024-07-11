#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)
import json
import lib.BasicMeasurement as basic
from lib.Database import Database

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "qmin"

  # Data Source
  db = Database(f"{dataset_dir}/combined/")
  #data_source = f"{dataset_dir}/combined/{measurement}/data"

  # Data Dest
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"

  
  data = []

  LIMIT = 1000
  num_loaded = 0
  # Walk database directory 
  for f in db.traverse_files(prefix=measurement):
    if num_loaded >= LIMIT:
      break

    with open(f, 'r') as f: # open nameserver file

      # Read, parse, filter data 
      sample = [basic.BasicMeasurement(json.loads(l)) for l in f if l != "\n"]
      num_loaded += len(sample)
      for i, s in enumerate(sample):

        if not s.cs_qmin():
          continue

        if True:
          print(f"\n Sample: nameserver: {s.get_resolver()} line {i}")
          iter = s.qmin_iterations(debug=True)
          print(f"QMIN Iter: {iter}")
          print(f"QMIN Full: {s.qmin_full()}")


