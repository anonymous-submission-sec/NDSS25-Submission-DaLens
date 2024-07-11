#! /usr/bin/env python3

import json
import csv

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
  parser = argparse.ArgumentParser(
    description="Takes Xmap output, filters it and produces a \
      resolver csv file to satisfy host information for a query pattern.")

  parser.add_argument("discovery_file", 
    help="Xmap resolver discovery output.")
  parser.add_argument("--o", default="resolvers.csv", metavar="resolver_file",
    help="Name of the output file used by query patterns")
  
  args = parser.parse_args()
  
  DISCOVERY_FILE = args.discovery_file
  RESOLVER_FILE = args.o

  assert RESOLVER_FILE.endswith(".csv"), f"Output file must be a .csv, not '{RESOLVER_FILE}'"
  
  res = read_enum_output(DISCOVERY_FILE)
  #print(f"Found {len(res)} responses") 
  #res = [el for el in res if el['repeat'] == False]
  #print(f"Found {len(res)} non-repeat responses") 
  #res = [el for el in res if el['dns_rcode'] == 0]
  #print(f"Found {len(res)} successful responses") 
  #res = [el for el in res if has_answer(el)]
  #print(f"Found {len(res)} correct responses") 
  
  #out = list()
  #for el in res:
  #  o = {
  #    "ns0": el['saddr'],
  #    "vp0": el['daddr'],
  #  }
  #  out.append(o)

  #write_resolver_file(out, RESOLVER_FILE)

  # Create Aggregate file
  data = list()
  for el in res:
    data.append({
      "ns0": el['saddr'],
      "vp0": el["daddr"],
      "rcode": el["dns_rcode"],
      "app_success": el["app_success"],
      #"correct_resolved": has_answer(el),
      "ts": el["timestamp_str"],
      #"question": el['dns_questions'][0]['name'],

    })
#  # Filter successful
#  data = [d for d in data if d['rcode'] == 0]
#  # Filter correct
#  data = [d for d in data if d['correct_resolved']]
  sortkey = lambda x: tuple([int(y) for y in x['ns0'].split(".")])
  #data = sorted(data, key=lambda x: int(x['ns0'].split(".")[0]))
  data = sorted(data, key=sortkey)
  write_resolver_file(data, RESOLVER_FILE)
  






