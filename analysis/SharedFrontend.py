#! /usr/bin/env python3



import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import json
from lib.Database import Database
from lib import BasicMeasurement as basic
import lib.plot as plot

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "shared_frontend"

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
        if not s.cs_shared_frontend():
          continue
        
        print(f"\nSample: nameserver {s.get_resolver()} line {i}")
        print(f"Shared Frontend: {s.shared_frontend(debug=True)}")



  ## Plot slices of 12 basic measurements in data
  #for i in range(0, len(data), 12):
  #  plot.plot_subplot(data[i:i+12], plot.subplot_logentry_timing, sub_x=4, sub_y=3)




