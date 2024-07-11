#! /usr/bin/env python3

import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import json
import common.jsonline as io
import lib.bindlog as bindlog
import common.encoding as encoding
import config as c
from lib.Database import Database

# Globals
client_suffix = "client"
server_suffix = "server"

file_format = "{pattern}-{suffix}"
#out_format = "{pattern}"

""" Distribute a single client / probe response file into the database."""
def distribute_client_file(raw_client_file, db, pattern):
  STATS_LOG.write(f"Distributing {raw_client_file}")
  stats = {
    "Measurements": 0,
    "JSON Decode Error": 0
  }
  with open(raw_client_file, "r") as f:
    for i, line in enumerate(f):
      stats['Measurements'] += 1
      try:
        d = json.loads(line)
      except json.JSONDecodeError as e:
        ERROR_LOG.write(f"JSON Decode Error: {e}, line {i} in {raw_client_file}\n")
        ERROR_LOG.write(line)
        stats['JSON Decode Error'] += 1
        continue

      ns = list(set([q['rr'] for q in d['queries']]))
      if len(ns) > 1: # If multiple resolvers involved, sort them by IP
        ns = sorted(ns, key=lambda x: tuple([int(i) for i in x.split(".")]))
      ns = ns[0]

      # Check if folder exists, if not create it
      folder = db.ns_folder(ns)
      if not os.path.exists(folder):
        os.makedirs(folder)

      client_file = f"{folder}/{file_format.format(pattern=pattern, suffix=client_suffix)}"
      with open(client_file, "a+") as f:
        f.write(line)
  # Print stats
  STATS_LOG.write(f"\tMeasurements processed: {stats['Measurements']}")
  STATS_LOG.write(f"\tJSON Decode Error: {stats['JSON Decode Error']}")
  STATS_LOG.write("")


""" Distribute a single server log file into the database."""
def distribute_server_log(raw_server_file, db, domain_suffixes:list, pattern, order:tuple=("ns", "vp")):
  STATS_LOG.write(f"Distributing {raw_server_file}")
  stats = {
    "irrelevant_entry": 0,
    "file_not_found": 0,
    "file_exists": 0,
    "unable_to_parse": 0,
    "unable_to_decode": 0
  }

  parser = bindlog.BindLog(c.RE_LOGENTRY)

  with open(raw_server_file, "r") as f:
    for line in f:
      # Skip empty lines
      if line == "\n":
        continue

      # Parse entry
      entry = parser.parse(line)
      if entry == None:
        ERROR_LOG.write(f"Unable to parse line in {raw_server_file}:\n")
        ERROR_LOG.write(line)
        stats['unable_to_parse'] += 1
        continue

      if not any([entry['query'].endswith(d) for d in domain_suffixes]): # e.g. qmin-tax.org
        stats['irrelevant_entry'] += 1
        continue

      ips = encoding.extract_id(entry['query'], order=order)
      if ips == None:
        stats['irrelevant_entry'] += 1
        continue
      else:
        # Sort rr by IP in case there are multiple
        try:
          entry['ns'] = sorted(ips['ns'], key=lambda x: tuple([int(i) for i in x.split(".")]))
          entry['vp'] = ips['vp']
        except Exception as e:
          ERROR_LOG.write(line)
          stats['unable_to_decode'] += 1
          continue

      ns = entry['ns'][0]
      
      # Check if client file exists
      client_file = f"{db.ns_folder(ns)}/{file_format.format(pattern=pattern, suffix=client_suffix)}"
      if not os.path.exists(client_file):
        stats['file_not_found'] += 1
        continue
      stats['file_exists'] += 1

      # Write log entries to separate server file
      server_file = f"{db.ns_folder(ns)}/{file_format.format(pattern=pattern, suffix=server_suffix)}"
      with open(server_file, "a+") as f:
        f.write(json.dumps(entry) + "\n")
  
  STATS_LOG.write(f"\tIrrelevant Entries: {stats['irrelevant_entry']}")
  STATS_LOG.write(f"\tEntries lacking a *-{client_suffix} file: {stats['file_not_found']}")
  STATS_LOG.write(f"\tEntries with a *-{client_suffix} file: {stats['file_exists']}")
  STATS_LOG.write(f"\tUnparsable Entries: {stats['unable_to_parse']}")
  STATS_LOG.write(f"\tEntries with no encoding: {stats['unable_to_decode']}")
  STATS_LOG.write("")

""" Combine client and server files into a single file with logentries field."""
def combine_files(db):
  STATS_LOG.write(f"Combining *-{client_suffix} and *-{server_suffix} files")
  stats = {
    "no_logentries": 0,
    "server_without_client": 0,
    "JSON_error": 0,
  }

  for server_file in db.traverse_files(suffix=server_suffix):

    # Check if client file exists
    client_file = server_file[:-len(server_suffix)] + client_suffix
    if not os.path.exists(client_file):
      ERROR_LOG.write(f"Server file without client file: {server_file}\n")
      stats['server_without_client'] += 1
      continue

    # Read server file
    with open(server_file, "r") as f:

      # Build map of 'vp' field of server entries to server entries
      vp_to_entry = {}
      for i, line in enumerate(f):
        try:
          d = json.loads(line)
        except json.JSONDecodeError as e:
          ERROR_LOG.write(f"JSON Decode Error: {e}, line {i} in {server_file}\n")
          ERROR_LOG.write(line)
          stats['JSON_error'] += 1
          continue
        # Create list if not existent
        if d['vp'] not in vp_to_entry:
          vp_to_entry[d['vp']] = []
        vp_to_entry[d['vp']].append(d)

    # Stream client file
    combined_file = server_file[:-len(server_suffix)-1]

    with open(client_file, "r") as f:
      with open(combined_file, "w") as f2:
        # Read client file
        for line in f:
          try:
            client_entry = json.loads(line)
          except json.JSONDecodeError as e:
            ERROR_LOG.write(f"JSON Decode Error: {e}, line {i} in {client_file}\n")
            ERROR_LOG.write(line)
            stats['JSON_error'] += 1
            continue
          # Get vp
          vp = list(set([q['vp'] for q in client_entry['queries']]))
          assert len(vp) == 1
          vp = vp[0]

          # add 'logentries' field to client entry
          if vp in vp_to_entry:
            client_entry['logentries'] = vp_to_entry[vp]
          else:
            client_entry['logentries'] = []
            stats['no_logentries'] += 1
          # Write combined entry to file
          f2.write(json.dumps(client_entry) + "\n")

    # Delete client and server file
    os.remove(client_file)
    os.remove(server_file)
  STATS_LOG.write("\tserver_without_client: " + str(stats['server_without_client']))
  STATS_LOG.write("\tno_logentries: " + str(stats['no_logentries']))
  STATS_LOG.write("\tJSON Decode Error: " + str(stats['JSON_error']))
  STATS_LOG.write("")


""" Move client files without corresponding server files to combined files with empty logentries field."""
def move_serverless_clients(db, pattern_suffix=""):
  STATS_LOG.write(f"Moving *-{client_suffix} files without corresponding *-{server_suffix} files")
  stats = {
    "client_without_server": 0,
    "JSON_error": 0
  }

  for client_file in db.traverse_files(suffix=client_suffix):

    # Check if server file exists
    server_file = client_file[:-len(client_suffix)] + server_suffix
    assert not os.path.exists(server_file), f"Server file without client file: {server_file}. Make sure to run combine_files first."
    stats['client_without_server'] += 1

    # Move client file to combined file with empty logentries
    combined_file = client_file[:-len(client_suffix) - 1] # remove suffix and dash

    with open(client_file, "r") as f:
      with open(combined_file, "w") as f2:
        # Create 'logentries' empty list for all basic measurements
        for i, line in enumerate(f):
          try:
            client_entry = json.loads(line)
          except json.JSONDecodeError as e:
            ERROR_LOG.write(f"JSON Decode Error: {e}, line {i} in {client_file}\n")
            ERROR_LOG.write(line)
            stats['JSON_error'] += 1
            continue

          client_entry['logentries'] = []
          f2.write(json.dumps(client_entry) + "\n")
    # Delete client file
    os.remove(client_file)

  STATS_LOG.write(f"\tclient_without_server: {stats['client_without_server']}")
  STATS_LOG.write(f"\tJSON Decode Error: {stats['JSON_error']}")
  STATS_LOG.write("")

""" Helper to write to file and stdout at once."""
class Tee(object):
  def __init__(self, name, mode):
    self.log = open(name, mode)
    self.stdout = sys.stdout
  def __del__(self):
    self.log.close()
  def write(self, data):
    self.log.write(data + "\n")
    self.stdout.write(data + "\n")

ERROR_LOG = None
STATS_LOG = None

if __name__ == "__main__":
  
  # Simple script to combine and associate client responses and nameserver log
  import argparse
  parser = argparse.ArgumentParser(description="Simple script to combine and associate client responses and nameserver logfile")
  
  subparsers = parser.add_subparsers(help="commands", dest='command', required=True)
  
  # Do all 4 steps in one go
  all_parser = subparsers.add_parser("all")
  all_parser.add_argument("src", help="source directory containing client and server files")
  all_parser.add_argument("dst",help="destination directory for combined files")

  # Distribute client files to measurement folder
  dist_c_parser = subparsers.add_parser("distribute_client")
  dist_c_parser.add_argument("src", help="source directory containing client and server files")
  dist_c_parser.add_argument("dst",help="destination directory for combined files")

  # Distribute relevant log entries for each server log
  dist_s_parser = subparsers.add_parser("distribute_server")
  dist_s_parser.add_argument("src", help="source directory containing client and server files")
  dist_s_parser.add_argument("dst", help="destination directory for combined files")

  # Combine client and server files
  combine_parser = subparsers.add_parser("combine")
  combine_parser.add_argument("src", help="source directory containing client and server files")
  combine_parser.add_argument("dst", help="destination directory for combined files")

  # Move lone client files, add an empty logentries field
  move_parser = subparsers.add_parser("move_serverless")
  move_parser.add_argument("src", help="source directory containing client and server files")
  move_parser.add_argument("dst", help="destination directory for combined files")
  
  args = parser.parse_args()

  # Init
  source = args.src if not args.src.endswith("/") else args.src[:-1]
  dest = args.dst if not args.dst.endswith("/") else args.dst[:-1]
  db = Database(f"{dest}")

  # Get pattern name
  PATTERN = source.split("/")[-1]
    
  # Copy zoneconfig and settings file
  if not os.path.exists(f"{dest}/zoneconf"):
    os.makedirs(f"{dest}/zoneconf")
  os.system(f"cp {source}/zoneconfig.json {dest}/zoneconf/{PATTERN}.json")
  if not os.path.exists(f"{dest}/settings"):
    os.makedirs(f"{dest}/settings")
  os.system(f"cp {source}/settings.json {dest}/settings/{PATTERN}.json")

  # Initialize logs
  if not os.path.exists(f"{dest}/combine_log"):
    os.makedirs(f"{dest}/combine_log")
  if args.command == "all":
    ERROR_LOG = open(f"{dest}/combine_log/{PATTERN}.error", "w")
    STATS_LOG = Tee(f"{dest}/combine_log/{PATTERN}.stats", "w")
  else:
    ERROR_LOG = open(f"{dest}/combine_log/{PATTERN}.error", "a")
    STATS_LOG = Tee(f"{dest}/combine_log/{PATTERN}.stats", "a")


  
  if args.command == "distribute_client" or args.command == "all":
    
    client_files = [f for f in os.listdir(source) if f.startswith("client")]
    assert len(client_files) > 0, "No client files found"
    
    assert os.path.exists(f"{source}/zoneconfig.json"), "zoneconfig.json not found"
    assert os.path.exists(f"{source}/settings.json"), "settings.json not found"

    for f in client_files:
      distribute_client_file(f"{source}/{f}", db, PATTERN)
  



  if args.command == "distribute_server" or args.command == "all":
    #source = args.src if not args.src.endswith("/") else args.src[:-1]
    #dest = args.dst if not args.dst.endswith("/") else args.dst[:-1]
    #db = Database(f"{dest}")
    
    #PATTERN = source.split("/")[-1]
    server_files = [f for f in os.listdir(source) if f.startswith("server")]
    assert len(server_files) > 0, "No server files found"
    RELEVANT_DOMAINS = [ns['DOMAIN'] for ns in c.NAMESERVERS.values()]

    decoding = ("ns", "vp")
    for f in server_files:
      distribute_server_log(f"{source}/{f}", db, RELEVANT_DOMAINS, PATTERN, order=decoding)



  if args.command == "combine" or args.command == "all":
    #dest = args.dst if not args.dst.endswith("/") else args.dst[:-1]
    #db = Database(f"{dest}")
    combine_files(db)



  if args.command == "move_serverless" or args.command == "all":
    #dest = args.dst if not args.dst.endswith("/") else args.dst[:-1]
    #db = Database(f"{dest}")
    move_serverless_clients(db)

  ERROR_LOG.close() 
