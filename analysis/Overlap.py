#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import json
import csv
from itertools import islice

from lib.Database import Database

""" Generate shared egress resolvers based on the egress IPs of a list of resolvers.
Args:
  egress_ip_file: file containing the egress IPs of the resolvers in the format generated by the agg_egress_ips function

  shared_egress_file: output file
  db: Database object used to fill in the properties of the resolvers:w
Returns:
  None
  """
def generate_shared_egress(egress_ip_file, shared_egress_file, db):

  shared_funcs = {
    "shared_frontend": {
      "process": lambda x: x.shared_frontend(),
      "filter": lambda x: x.cs_shared_frontend()
    }
  }
  rd0_funcs = {
    "rd0": {
      "process": lambda x: x.rd0_answers_honors(),
      "filter": lambda x: x.cs_rd0()
    }
  }
  # Output fields
  rr_vp_tuple = ["rr0", "rr1", "vp0"]
  stats = ["num_common_egress", "num_total_unique", "percent_overlap"]
  #properties = ["shared_rr0", "shared_rr1", "rd0_rr0", "rd0_rr1"]

  #fieldnames = rr_vp_tuple + properties + stats
  fieldnames = rr_vp_tuple + stats
  
  with open(shared_egress_file, 'w') as of:       # Open output file
    
    # Prepare writer
    writer = csv.DictWriter(of, fieldnames=fieldnames)
    writer.writeheader()

    with open(egress_ip_file, 'r') as f:
      
      for i, line in enumerate(f):                # Iterate over all resolvers
        
        if i % 100 == 0:          # Status update 
          print(f"Processed {i} lines")

        rr0 = json.loads(line)    # Load resolver 0

        with open(egress_ip_file, 'r') as f2:     # Iterate over all other resolvers
          for l2 in islice(f2, i+1, None):        # Skip already processed nameservers

            rr1 = json.loads(l2)  # Load resolver 1
            # Skip if resolvers have no common vantagepoints
            vps_common = set(rr0["vps"].keys()).intersection(set(rr1["vps"].keys()))
            if len(vps_common) == 0:
              continue
            
            # Create list of tuples (vp, common_egress)
            vps_egress_common = list() 
            for vp0 in vps_common:
              common = set(rr0["vps"][vp0]).intersection(set(rr1["vps"][vp0]))
              if len(common) > 0:
                vps_egress_common += [(vp0, common)]

            # Skip if vps have no common egress
            if len(vps_egress_common) == 0: 
              continue

            # Compute properties of interest 
            #shared_rr0 = db.process_resolver(rr0['ns'], shared_funcs)
            #shared_rr1 = db.process_resolver(rr1['ns'], shared_funcs)
            #rd0_rr0 = db.process_resolver(rr0['ns'], rd0_funcs)
            #rd0_rr1 = db.process_resolver(rr1['ns'], rd0_funcs)

            # TODO: filter output 
            for vp0, common in vps_egress_common: 
              
              total_unique = len(set(rr0["vps"][vp0] + rr1["vps"][vp0]))
              percent_overlap = round(len(common) / total_unique * 100, 1)
              r = {
                "rr0": rr0["ns"],
                "rr1": rr1["ns"],
                "vp0": vp0,
                "num_common_egress": len(common),
                "num_total_unique": total_unique,
                "percent_overlap": percent_overlap,

              }
              #if shared_rr0 != None and vp0 in shared_rr0:
              #  r['shared_rr0'] = shared_rr0[vp0]
              #if shared_rr1 != None and vp0 in shared_rr1:
              #  r['shared_rr1'] = shared_rr1[vp0]
              #if rd0_rr0 != None and vp0 in rd0_rr0:
              #  r['rd0_rr0'] = rd0_rr0[vp0]
              #if rd0_rr1 != None and vp0 in rd0_rr1:
              #  r['rd0_rr1'] = rd0_rr1[vp0]
              writer.writerow(r)

if __name__ == "__main__":
  
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("egress_ip_file", 
    help="Input file to be processed")
  parser.add_argument("egress_overlap_file", 
    help="Output file of shared egress resolvers")
  #parser.add_argument("database_dir", 
  #  help="Data directory of the original data to enhance the output file with additional columns.")
  args = parser.parse_args()

  # Working directory
  #db = Database(args.database_dir)

  #generate_shared_egress(args.egress_ip_file, args.egress_overlap_file, db)
  generate_shared_egress(args.egress_ip_file, args.egress_overlap_file, None)