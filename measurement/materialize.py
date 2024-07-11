#! /usr/bin/env python3

import csv
import json
import jsonschema as js

import os, sys
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import common.encoding as encoding
import lib.schemas as schemas
#import common.Materialization as m
import config as c
import lib.Writer as w


""" Fill in missing fields in the pattern file with the defaults from config.py"""
def pattern_set_defaults(pattern:dict):
  # Set Zone defaults
  for ns in pattern['nameservers']:
    for zone in pattern['nameservers'][ns]:
      # Set defaults for all records of a zone
      for rr in zone['records']:
        default = c.PATTERN_ZONE_DEFAULT
        for k in default.keys():
          rr.setdefault(k, default[k])

  # Set query defaults
  for q in pattern['queries']:
    default = c.PATTERN_QUERY_DEFAULT
    for k in default.keys():
      q.setdefault(k, default[k])

""" Extract all dynamic fields that are required for the given pattern"""
def pattern_get_required_columns(pattern: dict) -> set:
  required_columns = set()
  for dyn_f in DYNAMIC_FIELDS:
    # Go through all queries in the pattern
    for qt in pattern['queries']:
      # check if the dynamic field is set with a placeholder
      try:
        int(qt[dyn_f])
      except ValueError:
        required_columns.add(qt[dyn_f])
  return required_columns

""" Materialization class to materialize a pattern file with a given resolver file"""
class Materialization:

  def __init__(self, pattern: dict, materialize_dir: str, shard_after:int, skip_duplicate_check:bool):
    
    self.pattern = pattern
    
    self.zone_writer = w.ZoneWriter(materialize_dir, c.NAMESERVERS, shard_after, skip_duplicate_check)
    self.task_writer = w.TaskWriter(materialize_dir, c.CLIENT_HOSTS)
  
  def __del__(self):
    # Print statistics
    num_tasks = sum(self.task_writer.get_stats().values())
    num_records = sum(self.zone_writer.get_stats().values())
    num_servers = len(self.zone_writer.get_stats().keys())
    assert self.task_writer.shard_num == self.zone_writer.shard_num, "Something went wrong with the Writers.."
    num_shards = self.task_writer.shard_num + 1

    print(f"Materialized {num_tasks} querytasks and {num_records} RRs on {num_servers} nameserver(s) to {num_shards} shard(s).")

  """ Internal function to materialize a label."""
  def _materialize_label(self, label:str, resolver:dict):
    if label.startswith('$'):
      #assert label[1:] in c.NAMESERVERS, f"Unknown nameserver {label[1:]}"
      return c.NAMESERVERS[label[1:]]['DOMAIN']
    elif label.startswith('@'):
      #assert label[1:] in c.NAMESERVERS, f"Unknown nameserver {label[1:]}"
      return c.NAMESERVERS[label[1:]]['IP']
    elif label.startswith('#'):
      assert False
    elif label.startswith('enc'):
      enc_name = encoding.enc(label[4:-1], resolver)
      return enc_name
    else:
      return label # Literal, no substitution required

  """ Public function to materialize querytasks and Zone records for a given resolver"""
  def materialize(self, resolver: dict) -> None:
    # TODO: Check if ns and zone are available according to config
    
    # Create RRs for zone file
    ns_config = {} # materialized ns_config to pass on
    for ns in self.pattern['nameservers']:     # Iterate over all nameservers in the pattern
      ns_ip = c.NAMESERVERS[ns]['IP']   # Nameserver IP
      ns_config[ns_ip] = []
      for zone in self.pattern['nameservers'][ns]:   # Each might host multiple zones
        # For one zone on one nameserver, process all records
        zone_rrs = self._create_zone(resolver, zone['records'])
        
        # Write records to zone files
        zone_name = ".".join([self._materialize_label(l, resolver) for l in zone['zone'].split(".")]) 
        self.zone_writer.write(ns_ip, zone_name, zone_rrs)
        # Save materialized records
        ns_config[ns_ip].append({"zone": zone_name, "records": zone_rrs})

    # Create queries
    task = self._create_queries(resolver, ns_config)
    # Write queries to task files
    self.task_writer.write(resolver['vp0'], task)

    # Decide whether to shard
    if self.zone_writer.should_shard() or self.task_writer.should_shard():
      self.zone_writer.shard()
      self.task_writer.shard()

  """ Public function to materialize zone config with known values. Labels enc() that depend on resolver and vantage point are not materialized."""
  def materialize_zone_config(self):
    zoneconf = dict(self.pattern['nameservers'])
    # materialize all fields / labels except ones starting with enc()
    for ns in zoneconf:
      for zone in zoneconf[ns]:
        zone['zone'] = ".".join([self._materialize_label(l, None) for l in zone['zone'].split(".")]) # Zone should not contain any 'enc()' labels
        for rr in zone['records']:
          # Process record name
          labels = []
          for l in rr['name'].split("."):
            labels += [self._materialize_label(l, None)] if not l.startswith('enc(') else [l]
          rr['name'] = ".".join(labels)
          # Process record answer
          labels = [] 
          for l in rr['ans'].split("."):
            labels += [self._materialize_label(l, None)] if not l.startswith('enc(') else [l] 
          rr['ans'] = ".".join(labels)
          # Remove random_subdomains from zoneconf
          #del rr['random_subdomains']  # Remove random_subdomains from zoneconf
    # Replace nameserver names with IPs
    zoneconf2 = {}
    for ns in zoneconf.keys():
      ip = c.NAMESERVERS[ns]['IP']
      zoneconf2[ip] = zoneconf[ns]
    return zoneconf2
      
  """ Internal function to create zone file RRs for a given resolver"""
  def _create_zone(self, resolver: dict, records):

    rrs = []
    for entry in records:
      rr = dict(entry)

      # Process record name
      labels = [self._materialize_label(l, resolver) for l in entry['name'].split('.')]
      enc_name = ".".join(labels)
      if entry['random_subdomains']:
        enc_name = "*." + enc_name

      rr['name'] = enc_name

      # Process record answer
      # TODO: make sure NS records have domain as answer and A records have IP as answers
      # TODO: distinguish hardcoded IP vs @0 meta symbols, trouble: hardcoded IP AND domain are splittable with .
      if not encoding.is_ip(rr['ans']):
        labels = [self._materialize_label(l, resolver) for l in entry['ans'].split(".")]
        rr['ans'] = ".".join(labels)
      
      rrs.append(rr)

    return rrs 
 
  """ Internal function to create querytasks for a given resolver"""
  def _create_queries(self, resolver:dict, ns_config:dict=None) -> dict:
    materialized_queries = []

    for qp in self.pattern['queries']:
      # Copy fields from pattern
      q = dict(qp)

      # Substitute dynamic fields
      for f in DYNAMIC_FIELDS:
        try:
          int(qp[f])
        except ValueError:
          # Make sure the placeholder is in the resolver csv
          if qp[f] not in resolver.keys():
            print(f"This pattern requires a variable {f}, but '{qp[f]}' is not in the resolver file")
            exit(1)
          # If wait is not an integer, find the placeholder in the resolver csv
          q[f] = resolver[qp[f]]

      # Replace meta variables  
      q['rr'] = resolver[str(qp['rr'])].strip()

      q['vp'] = resolver[str(qp['vp'])].strip()

      labels = [self._materialize_label(l, resolver) for l in qp['query'].split('.')]
      q['query'] = ".".join(labels)

      materialized_queries.append(q)
    
    result = {
        "pattern": self.pattern['pattern'],
        "queries": materialized_queries,
      }
    if ns_config != None:
      result['nameservers'] = ns_config
    return result


DYNAMIC_FIELDS = ['wait', 'repeat', 'timeout']

if __name__ == "__main__"  :
  
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("pattern", help="Pattern file")
  parser.add_argument("resolverfile", help="Resolver file")
  parser.add_argument("--xprod", required=False, default=False, action="store_true", help="Cross product of all resolvers and vantage points")
  parser.add_argument("--split", required=False, default=False, action="store_true", help="Split querytasks equally across vantage points")
  parser.add_argument("--shift", required=False, default=0, type=int, help="Shift the split query tasks by one vantage point")
  parser.add_argument("--shard_after", required=False, default=c.MAX_ZONE_ENTRIES, type=int, help="Shard the zone and querytask files into multiple files")
  parser.add_argument("--skip-duplicate-check", required=False, default=False, action="store_true", help="Skip duplicate check for zone files")
  args = parser.parse_args()

  # Check arguments 
  assert args.shift < len(c.CLIENT_HOSTS), f"Shift must be smaller than number of vantage points ({len(c.CLIENT_HOSTS)})"
  assert args.shard_after > 0, "Shard after must be greater than 0"
  assert not (args.xprod and args.split), "Cannot use --xprod and --split at the same time"


  # Read query pattern file
  with open(args.pattern, 'r') as f:
    pattern = json.loads(f.read())
    js.validate(pattern, schemas.pattern_scheme)
  print(f"Loaded pattern '{pattern['pattern']}'")

  # Set missing fields to defaults
  pattern_set_defaults(pattern)

  # Preliminary checks on columns in resolver file
  with open(args.resolverfile, 'r') as f:
    
    # Only read header of the csv file
    reader = csv.DictReader(f)
    first_line = next(reader)

    # Check all required columns are present
    for r in pattern_get_required_columns(pattern):
      if r not in first_line.keys():
        print(f"This pattern requires a variable {r}, but '{r}' is not in the resolver file")
        exit(1)

    if args.xprod or args.split:
      # Check if resolver file contains vantage points, if so print a warning
      if 'vp0' in first_line.keys():
        print("WARNING: resolver file contains vantage points, and --xprod or --split flag is set")
        print("INFO: Ignoring vantage points in resolver file")
    else:
      # If neither resolver file contains vantage points, nor --xprod or --split flag is set, print a fatal error
      if 'vp0' not in first_line.keys():
        print("FATAL: resolver file does not contain vantage points, but --xprod and --split flags are not set")
        exit(1)
  
  # Clean materialized dir before starting  
  if not os.path.exists(c.MATERIALIZE_DIR):
    os.makedirs(c.MATERIALIZE_DIR)
  else:
    for f in os.listdir(c.MATERIALIZE_DIR):
      print(f"Removing {f} in {c.MATERIALIZE_DIR} from previous measurement")
      os.remove(os.path.join(c.MATERIALIZE_DIR, f))
    
  # Materialize
  with open(args.resolverfile, 'r') as f_resolver:
    
    # Get available vantage points
    vps = [host['IP'] for host in c.CLIENT_HOSTS]

    # Shift vantage points (useful for split mode)
    for _ in range(args.shift):
      vps.append(vps.pop(0))

    split_ind = 0 # used as index into vps for round robin

    # Initialize materialization object    
    m = Materialization(pattern, c.MATERIALIZE_DIR, args.shard_after, args.skip_duplicate_check)

    # Read resolver file line by line
    resolver_reader = csv.DictReader(f_resolver)
    for line in resolver_reader:

      if args.xprod: # Cross product of all resolvers and vantage points
        # Use all vantage points, set vantage point, materialize
        for vp in vps:
          line['vp0'] = vp
          m.materialize(line)

      elif args.split: # Split querytasks equally across vantage points
        # Set vantage point, increment round robin index, materialize
        line['vp0'] = vps[split_ind]
        split_ind = (split_ind + 1) % len(vps)
        m.materialize(line)

      else: # Materialize according to resolver file
        m.materialize(line)

    # Dump 'nameservers' field to results directory
    with open(os.path.join(c.RESULTS_DIR, 'zoneconfig.json'), 'w') as f:
      json.dump(m.materialize_zone_config(), f, indent=2)
  