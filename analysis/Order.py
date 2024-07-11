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
  measurement = "ordering_2"

  # Data Source
  db = Database(f"{dataset_dir}/combined-pairs")
  

  # Output
  out_file = f"{dataset_dir}/aggregated/{measurement}.csv"


  
  data = []

  LIMIT = 12
  total = 0
  num_loaded = 0
  results = 0
  # Walk database directory 

  of = open(out_file, "w") 
  writer = csv.DictWriter(of, fieldnames=["vantagepoint", "order_A", "order_B"])
  writer.writeheader()
  for file in db.traverse_files(prefix="order_cachebased"):
    if num_loaded >= LIMIT:
      break
    with open(file, 'r') as f: # open nameserver file

      # Read, parse, filter data 
      sample = [basic.BasicMeasurement(json.loads(l)) for l in f if l != "\n"]
      total += len(sample)
      #sample = [d for d in sample if d.cs_order_rd0based()]
      #sample = [d for d in sample if d.cs_order_cachebased()]
      for s in sample:
        r = None
        if s.cs_order_cachebased():
          r = s.order_cachebased()
        elif s.cs_order_rd0based():
          r = s.order_rd0based()
        else:
          continue
          
        if r is not None:
          results += 1
          writer.writerow({"vantagepoint": s.get_vantagepoint(), "order_A": r[0], "order_B": r[1]})
      data += sample
      num_loaded += len(sample)

  print(f"Loaded {num_loaded} samples, {results} results")
  print(f"Total: {total}")

  
  # Plot slices of 12 basic measurements in data
  for i in range(0, len(data), 12):
    print("hello")
    for s in data[i:i+12]:
      print(s.get_resolvers())
      #s.order_rd0based(debug=True)
    #plot.plot_subplot(data[i:i+12], plot.subplot_order_rd0based, sub_x=4, sub_y=3)
    plot.plot_subplot(data[i:i+12], plot.subplot_order_cachebased, sub_x=4, sub_y=3)
