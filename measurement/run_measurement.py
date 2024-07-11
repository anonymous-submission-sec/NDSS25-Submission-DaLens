#! /usr/bin/env python3

import sys, os
import shutil


current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)

import config as c
#import ..config as c

import engine.config as ec
#import engine.config as ec

import common.jsonline as io
#from ..common import jsonline as io
#import ..common.jsonline as io

from lib.BindCtl import BindCtl 
from lib.SessionCtl import SessionCtl 
import json


""" Install all zonefiles in source_dir on the nameservers in ns_config """
def install_zonefiles(source_dir:str, zonefiles:list, ns_config:dict):

  # Group zonefiles by nameserver
  ns_zonefiles = {} # ns_id -> [(zone_name, zonefile_name),..]
  for zf in zonefiles:
    # Split zonefile name of format "zone@<zonename>@<ns_ip>"
    zonename, ns_ip = zf.split('@')[1:]
    # Find corresponding nameserver in config.py
    ns = [n for n in ns_config if ns_config[n]['IP'] == ns_ip][0]

    # Add zonefile to list of zonefiles for this nameserver 
    if ns not in ns_zonefiles:
      ns_zonefiles[ns] = []
    ns_zonefiles[ns].append((zonename, f"{source_dir}/{zf}"))

  # Install zonefiles on nameservers
  for ns in ns_zonefiles:
    
    # Create BindCtl object for this nameserver
    ctl = BindCtl(ns_config[ns]['identity'], ns_config[ns]['user'], ns_config[ns]['IP'], **ns_config[ns]['bind_config'])
    
    # Install zonefiles as well as named.conf.local
    print(f"Installing zonefiles {','.join([z[0] for z in ns_zonefiles[ns]])} on nameserver {ns_config[ns]['IP']}..")
    ctl.install_zones(ns_zonefiles[ns])

    # Run checks on zone, config, and service
    for zn, _ in ns_zonefiles[ns]:
      ctl.check_zone(zn)
    ctl.check_config()
    ctl.status()

""" Prepare probetask files and copy them to remote hosts """
def prepare_tasks(source_dir:str, taskfiles:list, host_handles:list):
    

    # Parse taskfile names
    probe_files = {} # probe_ip -> taskfile
    for tf in taskfiles:
      probe_ip = tf.split('@')[1]
      probe_files[probe_ip] = f"{source_dir}/{tf}"

    # Make sure for each probe IP there is an actual probe in the config
    available_hosts = [h.ip for h in host_handles]
    for p in probe_files:
      assert p in available_hosts, f"Probe {p} in taskfile name not found in config.py"

    # Copy probetask file to remote host
    for ip in probe_files:
      
      # Find corresponding host handle
      handle = [h for h in host_handles if h.ip == ip][0]

      # Copy probetask file 
      print(f"Copying probetask file '{probe_files[ip]}' to remote host {ip}..", end=" ")
      remote_taskfile = f"~/{ENGINE_DIR}/{PROBETASK_TEMPLATE.format('-'.join(ip.split('.')))}"
      if handle.copy_file_to(probe_files[ip], remote_taskfile):
        print("Done!")
      else:
        print("Failed!")
        exit(1)


""" Check if a session with name session_name is running on any of the hosts. Return list of handles for hosts where it is running """
def running_sessions(host_handles:list, session_name:str):
  return [h for h in host_handles if h.session_running(session_name)]

""" Dump engine settings to file """
def dump_engine_settings(out_dir:str, out_file:str):
  with open(f"{out_dir}/{out_file}", 'w') as f:
    s = {
      "settings": {
        "max_timeouts": ec.MAX_FAILS,
        "num_workers": ec.NUM_WORKERS,
        "wait_policy": ec.WAIT_POLICY,
        "abort_policy": ec.ABORT_POLICY,
        "debug": ec.DEBUG
      }
    }
    json.dump(s, f)
  
if __name__ == "__main__"  :

  # Input / Output folders 
  MATERIALIZED_DIR = "materialized"

  RESULTS_DIR = "results"
  DEFAULT_SERVEROUT = "server{shard}@{ip}@.log"
  DEFAULT_CLIENTOUT = "client{shard}@{ip}@.json"
  SETTINGS_OUT = "settings.json"

  # Engine folders
  ENGINE_DIR = "engine"
  ENGINE_MANAGER = "manager.py"

  # Temporary Filename Templates, passed to the engine as arguments
  PROBETASK_TEMPLATE = "probetasks{}.json"
  PROBEOUT_TEMPLATE = "probeout{}.json"
  HOST_MANAGER_LOG = "log.txt"

  SESSION_NAME = "measurement"
  
  import argparse
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(help="commands", dest='command', required=True)

  # Run command
  run_parser = subparsers.add_parser("run")
  run_parser.add_argument("-s", "--shard", type=int, default=None, help="Shard number to run")
  # Status command 
  status_parser = subparsers.add_parser("status")
  # Retrieve command 
  retrieve_parser = subparsers.add_parser("retrieve")
  # Clean command
  retrieve_parser = subparsers.add_parser("clean")
  retrieve_parser = subparsers.add_parser("clean-zones")
  # Kill command
  retrieve_parser = subparsers.add_parser("kill")
  
  args = parser.parse_args()

  # Add command 'install-zones'

  # Load host handles
  host_handles = [SessionCtl(h['identity'], h['user'], h['IP']) for h in c.CLIENT_HOSTS]
  ns_handles = {}
  for ns in c.NAMESERVERS:
    ns_handles[ns] = BindCtl(c.NAMESERVERS[ns]['identity'], c.NAMESERVERS[ns]['user'], c.NAMESERVERS[ns]['IP'], **c.NAMESERVERS[ns]['bind_config'])

  
  if args.command == "kill":
    
    running = running_sessions(host_handles, SESSION_NAME) # Get host handles which have a running session
    if len(running) == 0:
      print(f"No session '{SESSION_NAME}' is currently running on any host.")
    else:
      for h in running:
        print(f"Terminating session '{SESSION_NAME}' on {h.ip}..", end=" ")
        status = "Done!" if h.kill_session(SESSION_NAME) else "Failed!"
        print(status)
        print("You may want to run 'clean' on all remote hosts to remove temporary files.")
    exit(0)

  if args.command == "clean-zones": 
    # Go through all nameservers and remove all zonefiles
    for ns in c.NAMESERVERS:
      #ctl = BindCtl(c.NAMESERVERS[ns]['identity'], c.NAMESERVERS[ns]['user'], c.NAMESERVERS[ns]['IP'], **c.NAMESERVERS[ns]['bind_config'])
      # Exclude persistent zones
      ns_handles[ns].clean_zones(keep=c.NAMESERVERS[ns]['persistent_zones'])
    

  if args.command == "clean": 
    
    print(f"Running 'make clean' in '~/{ENGINE_DIR}/' on all remote hosts..")
    fails = 0
    for h in host_handles:
      success = h.make_clean(f"~/{ENGINE_DIR}")
      if not success:
        print(f"Something went wrong on host {h.ip}..")
        fails += 1
    print(f"Done! {len(host_handles) - fails} out of {len(host_handles)} hosts succeeded.")
    exit(0)


  if args.command == "status":
    
    running = running_sessions(host_handles, SESSION_NAME)  # Get host handles which have a running session
    if len(running) == 0:
      print(f"No session '{SESSION_NAME}' is currently running on any host.")
    else:
      print(f"Session '{SESSION_NAME}' is currently running on {','.join([h.ip for h in running])}.")
    exit(0)


  if args.command == "run":
    
    # Task files are named "tasks<shard>@<probe_ip>"
    taskfiles = [f for f in os.listdir(MATERIALIZED_DIR) if f.startswith("tasks")]

    # Determine shard numbers
    shard_ids = list(set([f.split('@')[0][5:] for f in taskfiles]))
    print(f"Found {len(shard_ids)} shard(s): {','.join(sorted(shard_ids))}")
    if args.shard is None:
      assert len(shard_ids) == 1 and shard_ids[0] == "0", "Shard number not specified, but multiple shards found"
      args.shard = 0        # No need to filter taskfiles in this case
    else:
      assert str(args.shard) in shard_ids, f"Shard number {args.shard} not found in taskfiles"
      taskfiles = [f for f in taskfiles if f.startswith(f"tasks{args.shard}@")]
    print(f"Running shard {args.shard}")

    print(f"Checking if any host has an ongoing measurement..")
    running = running_sessions(host_handles, SESSION_NAME)  # Get host handles which have a running session
    if len(running) > 0:
      print(f"Session '{SESSION_NAME}' is already running on {','.join([h.ip for h in running])}.")
      print(f"Please terminate all sessions with name '{SESSION_NAME}' before running a new measurement.")
      exit(1)

    # Limit host handles to only those that are involved in the measurement
    host_handles = [h for h in host_handles if h.ip in [f.split('@')[1] for f in taskfiles]]
    # Limit ns_handles to only those that are involved in the measurement
    involved_ns = list(set([f.split('@')[2] for f in os.listdir(MATERIALIZED_DIR) if f.startswith("zone")]))
    print(f"Involving nameservers: {','.join(involved_ns)}")

    for h in host_handles:                              # Prepare hosts
      h.copy_folder_to(f"{ENGINE_DIR}", "~")            # Copy engine folder
    
    dump_engine_settings(RESULTS_DIR, SETTINGS_OUT)     # Write settings to results dir

    # Create empty file to signal which shard id is currently being processed
    id_file = open(f"{RESULTS_DIR}/shard-{args.shard}", 'w')
    id_file.close()

    prepare_tasks(MATERIALIZED_DIR, taskfiles, host_handles)       # Prepare tasks

    # Clean zones on and reduce main zone to minimum size on all nameservers 
    for ns in c.NAMESERVERS:
      if c.NAMESERVERS[ns]['IP'] not in involved_ns:
        continue
      print(f"Cleaning zones on nameserver {c.NAMESERVERS[ns]['IP']}..", end=" ")
      print(f"{ns_handles[ns].ip}..")
      ns_handles[ns].clean_zones(keep=c.NAMESERVERS[ns]['persistent_zones'])
      with open(f"{RESULTS_DIR}tmp.zone", 'w') as f:    # Write minimal zonefile to tmp.zone
        f.write("\n".join(c.NAMESERVERS[ns]['SOA']) + "\n")
      ns_handles[ns].install_zones([(c.NAMESERVERS[ns]['DOMAIN'], f"{RESULTS_DIR}tmp.zone")]) # Install minimal zonefile
      print(f"Done!")
    os.remove(f"{RESULTS_DIR}tmp.zone")

    # Zonefiles are named "zone<shard>@<zonename>@<ns_ip>"
    zonefiles = [f for f in os.listdir(MATERIALIZED_DIR) if f.startswith(f"zone{args.shard}@")]
    install_zonefiles(MATERIALIZED_DIR, zonefiles, c.NAMESERVERS)  # Prepare nameservers

    # Reset server logs
    for ns in c.NAMESERVERS:                            # Reset server logs
      if c.NAMESERVERS[ns]['IP'] not in involved_ns:
        continue
      print(f"Resetting server log on nameserver {c.NAMESERVERS[ns]['IP']}..", end=" ")
      status = []
      status += [ns_handles[ns].delete_logs()]
      status += [ns_handles[ns].restart()]
      status += [ns_handles[ns].status()]
      print(f"{all(status)}")

    # Start measurements, run manager on each remote host
    for h in host_handles:
      probe_id = '-'.join(h.ip.split('.'))
      cmd = f"cd {ENGINE_DIR} && ./{ENGINE_MANAGER} {PROBETASK_TEMPLATE.format(probe_id)} {h.ip} {PROBEOUT_TEMPLATE.format(probe_id)} 2>&1 | tee {HOST_MANAGER_LOG}"
      
      print(f"Starting measurement in detached session '{SESSION_NAME}' on {h.ip}", end=" ")
      status = "Done!" if h.run_session(SESSION_NAME, cmd) else "Failed! You may want to run 'kill' to terminate all measurement sessions."
      print(status)


  if args.command == "retrieve":

    shard_ids = [f.split('-')[1] for f in os.listdir(RESULTS_DIR) if f.startswith("shard-")]
    assert len(shard_ids) == 1, f"Found {len(shard_ids)} shard files, but expected exactly one"
    shard_id = shard_ids[0]

    # Find active probes
    active_probes = [f.split('@')[1] for f in os.listdir(MATERIALIZED_DIR) if f.startswith(f"tasks{shard_id}@")]
    print(f"Found {len(active_probes)} probes involved in the measurement: {','.join(active_probes)}")
    
    # Create host handles ONLY for the hosts that are being used
    host_handles = [h for h in host_handles if h.ip in active_probes]
    
    # Make sure all probes have exited their session
    print(f"Checking if any host has an ongoing measurement..")
    running = running_sessions(host_handles, SESSION_NAME)
    if len(running) > 0:
      print(f"Session '{SESSION_NAME}' is still running on {','.join([h.ip for h in running])}.")
      print(f"Please wait for all sessions to finish before retrieving results.")
      exit(1)
    
    # Make sure client results file exists on all probes
    print(f"Checking if all probes produced a result file..")
    have_results = 0
    for h in host_handles:
      probe_id = '-'.join(h.ip.split('.'))
      if h.file_exists(f"~/{ENGINE_DIR}/{PROBEOUT_TEMPLATE.format(probe_id)}"):
        have_results += 1
      else:
        print(f"Probe {h.ip} has no session running but {PROBEOUT_TEMPLATE.format(probe_id)} was not found.. failure")
    if have_results != len(host_handles):
      print(f"Not all probes produced a result file.. check logs manually")
      exit(1)
    
    # Retrieve server log from all involved nameservers
    involved_ns = list(set([f.split('@')[2] for f in os.listdir(MATERIALIZED_DIR) if f.startswith("zone")]))
    print(f"Involved nameservers: {','.join(involved_ns)}")
    #for ns_ip in involved_ns:
    for id, handle in ns_handles.items():
      print(f"Checking nameserver {id} with {handle.ip}..")
      if handle.ip not in involved_ns:
        print("continue")
        continue
      
      # Find corresponding nameserver in config.py
      #ns_id = [n for n in c.NAMESERVERS if c.NAMESERVERS[n]['IP'] == ns_ip][0]

      # Fetch server log
      print(f"Retrieve server log from remote host {handle.ip}..", end=" ")
      target_file = f"{RESULTS_DIR}/{DEFAULT_SERVEROUT.format(shard=shard_id, ip=handle.ip)}"
      handle.fetch_logs(target=target_file)
      print(f"Writing server log to '{target_file}'.")

    # Collect results from all probes
    print(f"Collecting results from all probes..")

    # Fetch results from remote
    for h in host_handles:
      probe_id = '-'.join(h.ip.split('.'))
      probe_file = PROBEOUT_TEMPLATE.format(probe_id)
      # Fetch results from remote
      target_file = f"{RESULTS_DIR}/{DEFAULT_CLIENTOUT.format(shard=shard_id, ip=h.ip)}"
      print(f"Copying probe results from remote host {h.ip}..", end=" ")
      status = "Done!" if h.copy_file_from(f"~/{ENGINE_DIR}/{probe_file}", f"{target_file}") else "FAILED!"
      print(status)

    # Remove shard file
    os.remove(f"{RESULTS_DIR}/shard-{shard_id}")


