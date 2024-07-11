#! /usr/bin/env python3

import os, sys

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

from lib.Database import Database
import lib.Aggregate as agg

if __name__ == "__main__":
  
  # Working directory
  dataset_dir = "public1000-3"
  

  # Data Source
  db = Database(f"{dataset_dir}/combined/")
  out_dir = f"{dataset_dir}/aggregated"


  # Data Dest
  out_file = f"all.csv"
  funcs = {
    "qmin": agg.Process_Qmin("qmin"),
    "enum": agg.Process_Enumerate("enum"),
    "chain_cname3": agg.Process_CnameChainlength("chain_cname3"),
    "maxfetch2": agg.Process_NumFetches("maxfetch2"),
    "rd0": agg.Process_Rd0("rd0"),
    "shared_frontend": agg.Process_SharedFrontend("shared_frontend"),
    "ttl0": agg.Process_TTL0("ttl0"),
    #"fanout-qmin2": agg.Process_MAF("fanout-qmin2", field_suffix="_FO-QM"),
    #"wchain-qmin": agg.Process_MAF("wchain-qmin", field_suffix="_WC11-QM9"),
    #"fanout-wchain": agg.Process_MAF("fanout-wchain", field_suffix="_FO-WC"),
    #"fanout-fanout": agg.Process_MAF("fanout-fanout", field_suffix="_FO8-FO8"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  ## Data Dest
  out_file = f"enum_thorough.csv"
  funcs = {
    "enum": agg.Process_EnumerateThorough("enum"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  
  # ==========================
  #   Amplification Patterns
  # ========================== 
  out_file = "maf.csv"    # For comparison
  funcs = {
    "fanout-fanout": agg.Process_MAF("fanout-fanout", field_suffix="_FO8-FO8"),
    "fanout-wchain": agg.Process_MAF("fanout-wchain", field_suffix="_FO6-WC6"),
    "wchain-qmin": agg.Process_MAF("wchain-qmin", field_suffix="_WC11-QM9"),
    "wchain-fanout2": agg.Process_MAF("wchain-fanout2", field_suffix="_WC6-FO6"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)


  out_file = "fo8-fo8.csv"
  funcs = {
    "maxfetch2": agg.Process_NumFetches("maxfetch2"),
    "fanout-fanout": agg.Process_MAF("fanout-fanout", field_suffix="_FO8-FO8"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  
  out_file = "fo6-wc6.csv"
  funcs = {
    "maxfetch2": agg.Process_NumFetches("maxfetch2"),
    "chain_cname3": agg.Process_CnameChainlength("chain_cname3"),
    "fanout-wchain": agg.Process_MAF("fanout-wchain", field_suffix="_FO6-WC6"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  
  out_file = "wc11-qm9.csv"
  funcs = {
    "qmin": agg.Process_Qmin("qmin"),
    "chain_cname3": agg.Process_CnameChainlength("chain_cname3"),
    "wchain-qmin": agg.Process_MAF("wchain-qmin", field_suffix="_WC11-QM9"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  
  out_file = "wc6-fo6.csv"
  funcs = {
    "maxfetch2": agg.Process_NumFetches("maxfetch2"),
    "chain_cname3": agg.Process_CnameChainlength("chain_cname3"),
    #"wchain-fanout": agg.Process_MAF("wchain-fanout", field_suffix="_WC6-FO6"),
    "wchain-fanout2": agg.Process_MAF("wchain-fanout2", field_suffix="_WC6-FO6"),
  }
  print(f"Process {out_file}")
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=False)
  
  #print("Processing egress IPs...") 

  out_file = f"egress.json"
  funcs = {
    "enum": agg.Process_EgressList('enum')
  }
  db.process_multiple_datasets(f"{out_dir}/{out_file}", funcs, group_by_rr=True, filetype='json')



