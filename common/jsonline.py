#! /usr/bin/env python3


import json
import csv

def read_jsonline(filename: str) -> list:
  with open(filename, 'r') as f:
    content = f.read().split('\n')
    return [json.loads(l) for l in content if l != None and l != ""]

def write_jsonline(dictlist: list, filename: str) -> None:
  with open(filename, 'w') as f:
    content = "\n".join([json.dumps(entry) for entry in dictlist])
    f.write(content)

def read_csv(filename:str) -> list:
  with open(filename, 'r') as f:
    reader = csv.DictReader(f)
    return [l for l in reader if l != None and l != ""]

def write_csv(total:list, filename:str) -> None:
  with open(filename, 'w') as f:
    writer = csv.DictWriter(f, fieldnames=total[0].keys())
    writer.writeheader()
    for e in total:
      writer.writerow(e)