#! /usr/bin/env python3


import sys, os
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import json
import common.jsonline as io
import lib.bindlog as bindlog
import pprint

import lib.basic_measurement as basic
import matplotlib.pyplot as plt
import numpy as np


if __name__ == "__main__":
  
  import argparse
  parser = argparse.ArgumentParser(description="Print quality statistics of a given combined data file.")

  parser.add_argument("combineddata", 
    help="Combined datafile in JSON")
  args = parser.parse_args()


  client_data = io.read_jsonline(args.combineddata)

  # Print configuration info
  #timeout = client_data[0]['timeout_after']
  #max_timeouts = client_data[0]['max_timeouts']

  #print(f"Configured timeout: {timeout}")
  #print(f"Max number of timeouts: {max_timeouts}")
  #if "concurrent" in client_data[0].keys():
  #  print(f"Concurrent Queries: {client_data[0]['concurrent']}")
  #print()

  data = [basic.BasicMeasurement(e) for e in client_data]

  patterns = list(set([e.get_pattern_name() for e in data]))
  print(f"Patterns: {patterns}")
  
  # Offline
  offline = [e for e in data if e.is_offline()]
  print(f"{0*' '}{'Offline:':<20}{len(offline):>4}")
  # Offline Logentries
  offline_logentries = [e for e in offline if e.has_logentries()]
  print(f"{2*' '}{'Have Logentries:':<20}{len(offline_logentries):>4}")

  # Online
  online = [e for e in data if e.is_online()]
  print(f"{0*' '}{'Online:':<20}{len(online):>4}")


  #neither = [e for e in data if not e.is_online() and not e.is_offline()]
  #for e in neither:
  #  print(e.all_noerror())
  #  print(e.any_nxdomain())
  #  print(e.any_noanswer())
  #  print()
  assert len(offline) + len(online) == len(client_data), "Bug in either is_offline or is_online"
  
  
  # Online Complete 
  complete = [e for e in online if e.result_complete()]
  print(f"{2*' '}{'Completed tasks:':<20}{len(complete):>4}")

  complete_all_noerror = [e for e in complete if e.check_status_all("NOERROR")]
  print(f"{4*' '}{'No timeouts:':<20}{len(complete_all_noerror):>4}")
  
  complete_any_timeouts = [e for e in complete if e.check_status_any("TIMEOUT")]
  print(f"{4*' '}{'Any timeouts:':<20}{len(complete_any_timeouts):>4}")

  complete_any_srvfail = [e for e in complete if e.check_status_any("SRVFAIL")]
  print(f"{4*' '}{'Any srvfail:':<20}{len(complete_any_srvfail):>4}")

  complete_any_noanswer = [e for e in complete if e.check_status_any("NOANSWER")]
  print(f"{4*' '}{'Any noanswer:':<20}{len(complete_any_noanswer):>4}")

  #weird = [e for e in complete if not e.any_timeouts() or not e.all_noerror()]
  #basic.print_measurement_stats(weird)

  # Online Partial
  partial = [e for e in online if e.result_partial()]
  print(f"{2*' '}{'Partial tasks:':<20}{len(partial):>4}")
  #assert len(complete) + len(partial) == len(online), "Bug in either result_complete or result_partial"

  # Online Logentries
  online_logentries = [e for e in online if e.has_logentries()]
  print(f"{2*' '}{'Have Logentries:':<20}{len(online_logentries):>4}")


  # NXDOMAIN
  nxdomain = [e for e in data if e.check_status_any("NXDOMAIN")]
  print(f"{0*' '}{'Have NXDOMAIN:':<20}{len(nxdomain):>4}")
  # REFUSED
  refused = [e for e in data if e.check_status_any("REFUSED")]
  print(f"{0*' '}{'Have REFUSED:':<20}{len(refused):>4}")
  # SRVFAIL
  srvfail = [e for e in data if e.check_status_any("SRVFAIL")]
  print(f"{0*' '}{'Have SRVFAIL:':<20}{len(srvfail):>4}")
  # NOANSWER
  
  #fig, ax = plt.subplots(nrows=2, ncols=2)
  #ax[0,0].set_title("Complete Dataset")
  #ax[0,0].pie([len(online), len(offline)], labels = ["Online", "Offline"], radius=3, center=(4,4))
  #ax[0,0].set(xlim=(0,8), ylim=(0,8))
  #ax[0,1].set_title("Online")
  #ax[0,1].pie([len(complete), len(partial)], labels = ["Complete", "Partial"], radius=3, center=(4,4))
  #ax[0,1].set(xlim=(0,8), ylim=(0,8))
  #ax[1,0].set_title("Complete")
  #ax[1,0].pie(
  #  [len(complete_all_noerror), len(complete_any_timeouts), len(complete_any_noanswer), len(complete_any_srvfail)], 
  #  labels = ["All NOERROR", "Any TIMEOUT", "Any NOANSWER", "Any SRVFAIL"], radius=3, center=(4,4))
  #ax[1,0].set(xlim=(0,8), ylim=(0,8))
  #plt.show()

  # Per measurement stats
  #basic.print_measurement_stats(offline)
  #print()
  #basic.print_timeout_stats(complete_any_timeouts)
  #basic.print_timeout_stats(partial)

  