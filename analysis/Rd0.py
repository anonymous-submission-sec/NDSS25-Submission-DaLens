#! /usr/bin/env python3


import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import json
from lib.Database import Database
from lib import BasicMeasurement as basic

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  measurement = "rd0"

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
      #sample = [d for d in sample if d.num_logentries()]
      num_loaded += len(sample)
      for i, s in enumerate(sample):
        #queries = [l['query'] for l in s.get_logentries() if l['query'].startswith("n")]
        if not s.cs_rd0():
          continue
        #if s.rd0_refuses_ignores():
        if s.num_logentries() > 3:
          print(f"\n Sample: nameserver: {s.get_resolver()} line {i}")
          mutex = s._rd0_debug()
          print(f"Honors: {s.rd0_honors()}")
          print(f"Answers: {s.rd0_answers()}")
          print(f"Answers Honors: {s.rd0_answers_honors()}")
          print(f"Answers Ignores: {s.rd0_answers_ignores()}")
          print(f"Refuses Honors: {s.rd0_refuses_honors()}")
          print(f"Refuses Ignores: {s.rd0_refuses_ignores()}")

          mutex = [s.rd0_answers_honors(), s.rd0_answers_ignores(), s.rd0_refuses_honors(), s.rd0_refuses_ignores()]
          if not sum(mutex) == 1:
            print("Mutex error")
            exit(1)

        #failover = s.max_fetch_failover(debug=True)
        #s.max_fetch_tries_on_fail(debug=True)
        #s.max_fetch_num_ns_tried(debug=True)