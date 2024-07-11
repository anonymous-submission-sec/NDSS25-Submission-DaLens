#! /usr/bin/env python3


import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import common.jsonline as io
import lib.bindlog as bindlog
import config as c

if __name__ == "__main__":
  
  # Simple script to combine and associate client responses and nameserver log
  import argparse
  parser = argparse.ArgumentParser(description="Simple script to combine and associate client responses and nameserver logfile")

  parser.add_argument("csvfiles", nargs="+",
    help="CSV files to combine")
  parser.add_argument("--joinkeys", "-j", nargs="+", default=["ns0", "vp0"],
                      help="Keys to join on")
  parser.add_argument("--output", "-o", default="default_out.csv",
    help="Output file")
  args = parser.parse_args()

  JOIN_KEYS = args.joinkeys
  # Read first file completely
  data = io.read_csv(args.csvfiles[0])

  # Assert join keys are present
  for k in JOIN_KEYS:
    assert k in data[0].keys(), f"Key '{k}' not present in data"

  all_fields = set(data[0].keys())
  # For all other files, open them one by one, and add all fields to the first file
  for f in args.csvfiles[1:]:
    print(f"Combining {f}")
    other_data = io.read_csv(f)
    # Assert no columns other than join keys share a name
    other_fields = set(other_data[0].keys())
    assert all_fields.intersection(other_fields) == set(JOIN_KEYS), f"Duplicate columns in {f}"
    all_fields = all_fields.union(other_fields)
    for d in data:
      # Find matching entry in other_data
      match = [o for o in other_data if all([o[k] == d[k] for k in JOIN_KEYS])]
      assert len(match) == 1, f"Found {len(match)} matches for {d} in {f}"
      match = match[0]
      # Add all fields to d
      for k in match.keys():
        if k not in d.keys():
          d[k] = match[k]

    # Remove all entries that were not matched, i.e. have a missing column
    data = [d for d in data if all([k in d.keys() for k in all_fields])]

  # Write combined data to file
  io.write_csv(data, args.output)
